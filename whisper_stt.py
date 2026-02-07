# import queue
# import time
# import threading
# import sys
# import numpy as np
# import sounddevice as sd
# import whisper
# import librosa
# import torch
# from silero_vad import load_silero_vad, get_speech_timestamps

# # ==========================
# # CONFIG
# # ==========================
# SAMPLE_RATE = 16000
# CHUNK_SEC = 4.0
# OVERLAP_SEC = 0.5
# DEVICE = "cpu"

# OUTPUT_TXT = "final_transcript.txt"

# # ==========================
# # DERIVED CONSTANTS (FIXED)
# # ==========================
# CHUNK_SAMPLES = int(CHUNK_SEC * SAMPLE_RATE)
# OVERLAP_SAMPLES = int(OVERLAP_SEC * SAMPLE_RATE)
# STEP_SAMPLES = CHUNK_SAMPLES - OVERLAP_SAMPLES

# CHUNK_BYTES = CHUNK_SAMPLES * 2
# OVERLAP_BYTES = OVERLAP_SAMPLES * 2
# STEP_BYTES = STEP_SAMPLES * 2

# # ==========================
# # GLOBAL STOP FLAG
# # ==========================
# stop_recording = threading.Event()

# # ==========================
# # LOAD MODELS
# # ==========================
# whisper_model = whisper.load_model("base", device=DEVICE)
# vad_model = load_silero_vad()
# _whisper_lock = threading.Lock()

# # ==========================
# # AUDIO QUEUE
# # ==========================
# audio_q: queue.Queue[np.ndarray] = queue.Queue()

# def audio_callback(indata, frames, time_info, status):
#     if status:
#         print(status, file=sys.stderr)
#     audio_q.put(indata.astype(np.float32, copy=True))

# # ==========================
# # KEYBOARD STOP
# # ==========================
# def wait_for_enter():
#     input("\n⛔ Press ENTER to stop recording...\n")
#     stop_recording.set()

# # ==========================
# # UTILS
# # ==========================
# def rms_db(signal: np.ndarray) -> float:
#     rms = np.sqrt(np.mean(signal ** 2))
#     return float(20 * np.log10(rms + 1e-8))

# def pitch_stats(signal: np.ndarray):
#     pitches, mags = librosa.piptrack(
#         y=signal,
#         sr=SAMPLE_RATE,
#         fmin=50,
#         fmax=300
#     )

#     mask = mags > np.percentile(mags, 85)
#     pitch_vals = pitches[mask]

#     if pitch_vals.size == 0:
#         return 0.0, 0.0

#     return float(np.mean(pitch_vals)), float(np.std(pitch_vals))

# # ==========================
# # CONFIDENCE SCORING
# # ==========================
# def confidence_score(pitch_std: float, energy_variance: float) -> float:
#     pitch_norm = min(pitch_std / 90.0, 1.0)
#     pitch_score = 1.0 - pitch_norm

#     energy_norm = min(energy_variance / 5.0, 1.0)
#     energy_score = energy_norm

#     confidence = 0.65 * pitch_score + 0.35 * energy_score
#     return round(float(np.clip(confidence, 0.0, 1.0)), 2)

# # ==========================
# # TRANSCRIPT MERGE (SAFE)
# # ==========================
# def merge_transcripts(prev: str, new: str, max_overlap_words: int = 30) -> str:
#     """
#     Merge previous and new transcript by finding an overlapping suffix/prefix.
#     If no exact overlap is found, keep the longer segment or append the new text.
#     """
#     # nothing previously transcribed
#     if not prev:
#         return new

#     # If the new transcript already contains the previous transcript, return new
#     if prev in new:
#         return new

#     prev_words = prev.split()
#     new_words = new.split()
#     max_k = min(len(prev_words), len(new_words), max_overlap_words)

#     # look for overlap of up to max_k words at the boundary
#     for k in range(max_k, 0, -1):
#         if prev_words[-k:] == new_words[:k]:
#             # overlap found: append only the non-overlapping part
#             return prev + " " + " ".join(new_words[k:])

#     # fallback: if the new transcript is shorter, keep the previous
#     if len(new_words) <= len(prev_words):
#         return prev

#     # otherwise append the new text
#     return prev + " " + new

# # ==========================
# # TRANSCRIBE PCM16 CHUNK
# # ==========================
# def transcribe_pcm16_chunk(pcm16_bytes: bytes) -> str:
#     if len(pcm16_bytes) < SAMPLE_RATE * 2:
#         return ""

#     audio = np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32) / 32768.0
#     return transcribe_chunk(audio)

# # ==========================
# # TRANSCRIBE FLOAT32 CHUNK
# # ==========================
# def transcribe_chunk(audio_float32: np.ndarray) -> str:
#     if audio_float32.size < SAMPLE_RATE:
#         return ""

#     with _whisper_lock:
#         result = whisper_model.transcribe(
#             np.ascontiguousarray(audio_float32, dtype=np.float32),
#             language="en",
#             temperature=0.0,
#             condition_on_previous_text=True,
#             no_speech_threshold=0.4
#         )

#     return result["text"].strip()

# # ==========================
# # MAIN STREAMING ASR
# # ==========================
# def run_streaming_asr():
#     buffer = np.zeros(0, dtype=np.float32)
#     running_transcript = ""
#     audio_stats = []

#     threading.Thread(target=wait_for_enter, daemon=True).start()

#     with sd.InputStream(
#         samplerate=SAMPLE_RATE,
#         channels=1,
#         dtype="float32",
#         callback=audio_callback
#     ):
#         print("🎙 Listening...")

#         while not stop_recording.is_set():
#             chunk = audio_q.get()
#             chunk = chunk.flatten()
#             buffer = np.concatenate([buffer, chunk])

#             # ---- VAD (unchanged) ----
#             _ = get_speech_timestamps(
#                 torch.from_numpy(chunk),
#                 vad_model,
#                 sampling_rate=SAMPLE_RATE
#             )

#             # ---- Process chunk ----
#             while buffer.shape[0] >= CHUNK_SAMPLES:
#                 audio_input = buffer[:CHUNK_SAMPLES]
#                 buffer = buffer[STEP_SAMPLES:]

#                 text = transcribe_chunk(audio_input)
#                 if text:
#                     print(f"🧩 CHUNK TRANSCRIPT: {text}")
#                     running_transcript = merge_transcripts(running_transcript, text)

#                     vol = rms_db(audio_input)
#                     pitch_mean, pitch_std = pitch_stats(audio_input)

#                     audio_stats.append({
#                         "volume_db": vol,
#                         "pitch_mean": pitch_mean,
#                         "pitch_std": pitch_std,
#                         "duration": CHUNK_SEC,
#                         "words": len(text.split())
#                     })

#     # ==========================
#     # SAVE FINAL TRANSCRIPT
#     # ==========================
#     with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
#         f.write(running_transcript.strip())

#     # ==========================
#     # FINAL METRICS
#     # ==========================
#     avg_volume = np.mean([a["volume_db"] for a in audio_stats])
#     pitch_mean = np.mean([a["pitch_mean"] for a in audio_stats])
#     pitch_std = np.mean([a["pitch_std"] for a in audio_stats])
#     energy_var = np.var([a["volume_db"] for a in audio_stats])

#     confidence = confidence_score(pitch_std, energy_var)

#     return {
#         "transcript": running_transcript.strip(),
#         "confidence_metrics": {
#             "avg_volume_db": round(float(avg_volume), 2),
#             "pitch_mean_hz": round(float(pitch_mean), 2),
#             "pitch_std_hz": round(float(pitch_std), 2),
#             "energy_variance": round(float(energy_var), 4),
#             "confidence_score": confidence
#         }
#     }

# # ==========================
# # RUN
# # ==========================
# if __name__ == "__main__":
#     result = run_streaming_asr()

#     print("\n📝 FINAL TRANSCRIPT:")
#     print(result["transcript"])

#     print(f"\n💾 Saved transcript to: {OUTPUT_TXT}")

#     print("\n📊 CONFIDENCE METRICS:")
#     print(result["confidence_metrics"])
"""
Updated streaming ASR module for SnapInterview.

This file contains helper functions for splitting PCM16 audio into overlapping chunks,
transcribing each chunk with Whisper, merging the resulting transcripts, and
calculating simple audio metrics.  The `merge_transcripts` function has been
improved to use case-insensitive matching and to ignore trailing punctuation
when finding overlaps, ensuring that partial sentences spanning multiple
windows are merged correctly.
"""

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
# DERIVED CONSTANTS (FIXED)
# ==========================
CHUNK_SAMPLES = int(CHUNK_SEC * SAMPLE_RATE)
OVERLAP_SAMPLES = int(OVERLAP_SEC * SAMPLE_RATE)
STEP_SAMPLES = CHUNK_SAMPLES - OVERLAP_SAMPLES

CHUNK_BYTES = CHUNK_SAMPLES * 2
OVERLAP_BYTES = OVERLAP_SAMPLES * 2
STEP_BYTES = STEP_SAMPLES * 2

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
    """Callback for `sounddevice.InputStream` to enqueue audio frames."""
    if status:
        print(status, file=sys.stderr)
    audio_q.put(indata.astype(np.float32, copy=True))


def wait_for_enter():
    """Helper function for the CLI streaming example: stop on ENTER."""
    input("\n⛔ Press ENTER to stop recording...\n")
    stop_recording.set()

# ==========================
# UTILS
# ==========================
def rms_db(signal: np.ndarray) -> float:
    rms = np.sqrt(np.mean(signal ** 2))
    return float(20 * np.log10(rms + 1e-8))


def pitch_stats(signal: np.ndarray):
    pitches, mags = librosa.piptrack(
        y=signal,
        sr=SAMPLE_RATE,
        fmin=50,
        fmax=300,
    )

    mask = mags > np.percentile(mags, 85)
    pitch_vals = pitches[mask]

    if pitch_vals.size == 0:
        return 0.0, 0.0

    return float(np.mean(pitch_vals)), float(np.std(pitch_vals))


def confidence_score(pitch_std: float, energy_variance: float) -> float:
    pitch_norm = min(pitch_std / 90.0, 1.0)
    pitch_score = 1.0 - pitch_norm

    energy_norm = min(energy_variance / 5.0, 1.0)
    energy_score = energy_norm

    confidence = 0.65 * pitch_score + 0.35 * energy_score
    return round(float(np.clip(confidence, 0.0, 1.0)), 2)

# ==========================
# TRANSCRIPT MERGE (SAFE)
# ==========================
def merge_transcripts(prev: str, new: str, max_overlap_words: int = 30) -> str:
    """
    Merge previous and new transcript by finding the longest overlapping
    suffix/prefix.  Word comparison is case-insensitive and ignores leading or
    trailing punctuation.  If no overlap is found, append the new text to the
    previous transcript.

    Args:
        prev: The transcript accumulated so far.
        new:  The transcript of the latest audio window.
        max_overlap_words: Maximum words to consider when looking for overlap.

    Returns:
        A merged transcript string.
    """
    # nothing previously transcribed
    if not prev:
        return new

    # If the new transcript already contains the previous transcript, return new
    if prev in new:
        return new

    import string
    prev_words_raw = prev.split()
    new_words_raw = new.split()

    # Normalize words by stripping punctuation and converting to lowercase
    def normalize_word(w: str) -> str:
        return w.strip(string.punctuation).lower()

    prev_words_norm = [normalize_word(w) for w in prev_words_raw]
    new_words_norm = [normalize_word(w) for w in new_words_raw]

    max_k = min(len(prev_words_norm), len(new_words_norm), max_overlap_words)

    # look for the largest suffix/prefix overlap
    for k in range(max_k, 0, -1):
        if prev_words_norm[-k:] == new_words_norm[:k]:
            # overlap found: append only the non-overlapping raw new words
            return prev + " " + " ".join(new_words_raw[k:])

    # no overlap found; append the new text
    return prev + " " + new

# ==========================
# TRANSCRIBE PCM16 CHUNK
# ==========================
def transcribe_pcm16_chunk(pcm16_bytes: bytes) -> str:
    """Transcribe a 16-bit PCM buffer into text with Whisper."""
    if len(pcm16_bytes) < SAMPLE_RATE * 2:
        return ""

    audio = np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    return transcribe_chunk(audio)

# ==========================
# TRANSCRIBE FLOAT32 CHUNK
# ==========================
def transcribe_chunk(audio_float32: np.ndarray) -> str:
    """Transcribe a float32 numpy array of audio samples with Whisper."""
    if audio_float32.size < SAMPLE_RATE:
        return ""

    with _whisper_lock:
        result = whisper_model.transcribe(
            np.ascontiguousarray(audio_float32, dtype=np.float32),
            language="en",
            temperature=0.0,
            condition_on_previous_text=True,
            no_speech_threshold=0.4,
        )

    return result["text"].strip()

# ==========================
# MAIN STREAMING ASR
# ==========================
def run_streaming_asr():
    """
    Example command-line streaming ASR loop.  Records from the microphone and
    prints and saves the transcript.  Not used by the SnapInterview server.
    """
    buffer = np.zeros(0, dtype=np.float32)
    running_transcript = ""
    audio_stats = []

    threading.Thread(target=wait_for_enter, daemon=True).start()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=audio_callback,
    ):
        print("🎙 Listening...")

        while not stop_recording.is_set():
            chunk = audio_q.get()
            chunk = chunk.flatten()
            buffer = np.concatenate([buffer, chunk])

            # run VAD (unused but can trigger pre-processing)
            _ = get_speech_timestamps(
                torch.from_numpy(chunk),
                vad_model,
                sampling_rate=SAMPLE_RATE,
            )

            # process audio in fixed windows
            while buffer.shape[0] >= CHUNK_SAMPLES:
                audio_input = buffer[:CHUNK_SAMPLES]
                buffer = buffer[STEP_SAMPLES:]

                text = transcribe_chunk(audio_input)
                if text:
                    print(f"🧩 CHUNK TRANSCRIPT: {text}")
                    running_transcript = merge_transcripts(running_transcript, text)

                    vol = rms_db(audio_input)
                    pitch_mean, pitch_std = pitch_stats(audio_input)

                    audio_stats.append({
                        "volume_db": vol,
                        "pitch_mean": pitch_mean,
                        "pitch_std": pitch_std,
                        "duration": CHUNK_SEC,
                        "words": len(text.split()),
                    })

    # write final transcript to file
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(running_transcript.strip())

    # calculate simple audio metrics
    avg_volume = np.mean([a["volume_db"] for a in audio_stats]) if audio_stats else 0.0
    pitch_mean = np.mean([a["pitch_mean"] for a in audio_stats]) if audio_stats else 0.0
    pitch_std = np.mean([a["pitch_std"] for a in audio_stats]) if audio_stats else 0.0
    energy_var = np.var([a["volume_db"] for a in audio_stats]) if audio_stats else 0.0

    confidence = confidence_score(pitch_std, energy_var)

    return {
        "transcript": running_transcript.strip(),
        "confidence_metrics": {
            "avg_volume_db": round(float(avg_volume), 2),
            "pitch_mean_hz": round(float(pitch_mean), 2),
            "pitch_std_hz": round(float(pitch_std), 2),
            "energy_variance": round(float(energy_var), 4),
            "confidence_score": confidence,
        },
    }


if __name__ == "__main__":
    # simple CLI test
    result = run_streaming_asr()
    print("\n📝 FINAL TRANSCRIPT:")
    print(result["transcript"])
    print(f"\n💾 Saved transcript to: {OUTPUT_TXT}")
    print("\n📊 CONFIDENCE METRICS:")
    print(result["confidence_metrics"])