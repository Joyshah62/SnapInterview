import queue
import time
import threading
import sys
import numpy as np
import sounddevice as sd
import whisper
import librosa
import torch
from silero_vad import load_silero_vad, get_speech_timestamps

# ==========================
# CONFIG
# ==========================
SAMPLE_RATE = 16000
CHUNK_SEC = 4.0
OVERLAP_SEC = 0.5
DEVICE = "cpu"

OUTPUT_TXT = "final_transcript.txt"

# ==========================
# GLOBAL STOP FLAG
# ==========================
stop_recording = threading.Event()

# ==========================
# LOAD MODELS
# ==========================
whisper_model = whisper.load_model("base", device=DEVICE)
vad_model = load_silero_vad()
_whisper_lock = threading.Lock()

# ==========================
# AUDIO QUEUE
# ==========================
audio_q: queue.Queue[np.ndarray] = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    audio_q.put(indata.astype(np.float32, copy=True))

# ==========================
# KEYBOARD STOP (SAFE)
# ==========================
def wait_for_enter():
    input("\n⛔ Press ENTER to stop recording...\n")
    stop_recording.set()

# ==========================
# UTILS
# ==========================
def rms_db(signal: np.ndarray) -> float:
    rms = np.sqrt(np.mean(signal ** 2))
    return float(20 * np.log10(rms + 1e-8))

def pitch_stats(signal: np.ndarray):
    signal = signal.astype(np.float32, copy=False)

    pitches, mags = librosa.piptrack(
        y=signal,
        sr=SAMPLE_RATE,
        fmin=50,
        fmax=300
    )

    mask = mags > np.percentile(mags, 85)
    pitch_vals = pitches[mask]

    if pitch_vals.size == 0:
        return 0.0, 0.0

    return float(np.mean(pitch_vals)), float(np.std(pitch_vals))

# ==========================
# CONFIDENCE SCORING
# ==========================
def confidence_score(pitch_std: float, energy_variance: float) -> float:
    pitch_norm = min(pitch_std / 90.0, 1.0)
    pitch_score = 1.0 - pitch_norm

    energy_norm = min(energy_variance / 5.0, 1.0)
    energy_score = energy_norm

    confidence = 0.65 * pitch_score + 0.35 * energy_score
    return round(float(np.clip(confidence, 0.0, 1.0)), 2)

# ==========================
# TRANSCRIPT MERGE (BOUNDARY ONLY)
# ==========================
def merge_transcripts(prev: str, new: str, max_overlap_words: int = 30) -> str:
    if not prev:
        return new

    prev_words = prev.split()
    new_words = new.split()

    max_k = min(len(prev_words), len(new_words), max_overlap_words)

    for k in range(max_k, 0, -1):
        if prev_words[-k:] == new_words[:k]:
            return prev + " " + " ".join(new_words[k:])

    return prev + " " + new

CHUNK_BYTES = int(CHUNK_SEC * SAMPLE_RATE * 2)
OVERLAP_BYTES = int((CHUNK_SEC - OVERLAP_SEC) * SAMPLE_RATE * 2)


def transcribe_pcm16_chunk(pcm16_bytes: bytes) -> str:
    if len(pcm16_bytes) < SAMPLE_RATE * 2:
        return ""
    audio_int16 = np.frombuffer(pcm16_bytes, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0
    return transcribe_chunk(audio_float32)


# ==========================
# TRANSCRIBE SINGLE CHUNK (FLOAT32 NUMPY)
# ==========================
def transcribe_chunk(audio_float32: "np.ndarray") -> str:
    if audio_float32.size < SAMPLE_RATE:
        return ""
    with _whisper_lock:
        result = whisper_model.transcribe(
            np.ascontiguousarray(audio_float32, dtype=np.float32),
            language="en",
            temperature=0.0,
            condition_on_previous_text=False,
        )
    return result["text"].strip()


# ==========================
# TRANSCRIBE FROM WEBSOCKET CHUNKS (PCM16 BYTES)
# ==========================
def transcribe_from_pcm16_bytes(pcm16_bytes: bytes, output_txt: str = "final_transcript.txt") -> str:
    if not pcm16_bytes:
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("")
        return ""
    audio_int16 = np.frombuffer(pcm16_bytes, dtype=np.int16)
    buffer = audio_int16.astype(np.float32) / 32768.0
    chunk_texts = []
    offset = 0
    chunk_samples = int(CHUNK_SEC * SAMPLE_RATE)
    overlap_samples = int((CHUNK_SEC - OVERLAP_SEC) * SAMPLE_RATE)
    while offset + chunk_samples <= buffer.shape[0]:
        audio_input = buffer[offset : offset + chunk_samples]
        text = transcribe_chunk(audio_input)
        if text:
            chunk_texts.append(text)
        offset += overlap_samples
    if offset < buffer.shape[0] and buffer.shape[0] - offset > SAMPLE_RATE:
        remainder = buffer[offset:]
        text = transcribe_chunk(remainder)
        if text:
            chunk_texts.append(text)
    final_text = ""
    for t in chunk_texts:
        final_text = merge_transcripts(final_text, t)
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(final_text.strip())
    return final_text.strip()


# ==========================
# MAIN LOOP
# ==========================
def run_streaming_asr():
    buffer = np.zeros(0, dtype=np.float32)
    chunk_texts = []            # ✅ collect chunks
    audio_stats = []

    threading.Thread(target=wait_for_enter, daemon=True).start()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=audio_callback
    ):
        print("🎙 Listening...")

        while not stop_recording.is_set():
            chunk = audio_q.get()
            chunk = chunk.flatten()
            buffer = np.concatenate([buffer, chunk])

            # ---- Silero VAD (unchanged) ----
            _ = get_speech_timestamps(
                torch.from_numpy(chunk),
                vad_model,
                sampling_rate=SAMPLE_RATE
            )

            # ---- Process 4s chunk ----
            if buffer.shape[0] >= int(CHUNK_SEC * SAMPLE_RATE):
                audio_input = buffer[: int(CHUNK_SEC * SAMPLE_RATE)]
                buffer = buffer[int((CHUNK_SEC - OVERLAP_SEC) * SAMPLE_RATE):]

                audio_input = np.ascontiguousarray(audio_input, dtype=np.float32)

                result = whisper_model.transcribe(
                    audio_input,
                    language="en",
                    temperature=0.0,
                    condition_on_previous_text=False
                )

                text = result["text"].strip()
                if text:
                    print(f"🧩 CHUNK TRANSCRIPT: {text}")
                    chunk_texts.append(text)   # ✅ store chunk

                    vol = rms_db(audio_input)
                    pitch_mean, pitch_std = pitch_stats(audio_input)

                    audio_stats.append({
                        "volume_db": vol,
                        "pitch_mean": pitch_mean,
                        "pitch_std": pitch_std,
                        "duration": CHUNK_SEC,
                        "words": len(text.split())
                    })

    # ==========================
    # MERGE FINAL TRANSCRIPT
    # ==========================
    final_text = ""
    for t in chunk_texts:
        final_text = merge_transcripts(final_text, t)

    # ==========================
    # SAVE TO TXT FILE
    # ==========================
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(final_text.strip())

    # ==========================
    # FINAL METRICS
    # ==========================
    avg_volume = np.mean([a["volume_db"] for a in audio_stats])
    pitch_mean = np.mean([a["pitch_mean"] for a in audio_stats])
    pitch_std = np.mean([a["pitch_std"] for a in audio_stats])
    energy_var = np.var([a["volume_db"] for a in audio_stats])

    confidence = confidence_score(pitch_std, energy_var)

    return {
        "transcript": final_text.strip(),
        "confidence_metrics": {
            "avg_volume_db": round(float(avg_volume), 2),
            "pitch_mean_hz": round(float(pitch_mean), 2),
            "pitch_std_hz": round(float(pitch_std), 2),
            "energy_variance": round(float(energy_var), 4),
            "confidence_score": confidence
        }
    }

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    result = run_streaming_asr()

    print("\n📝 FINAL TRANSCRIPT:")
    print(result["transcript"])

    print(f"\n💾 Saved transcript to: {OUTPUT_TXT}")

    print("\n📊 CONFIDENCE METRICS:")
    print(result["confidence_metrics"])