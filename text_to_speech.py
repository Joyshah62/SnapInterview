import os
from enum import Enum
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# =========================================================
# ENV + CLIENT
# =========================================================
load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ ELEVENLABS_API_KEY not found")

client = ElevenLabs(api_key=API_KEY)

# =========================================================
# QUESTION TYPES
# =========================================================
class QuestionType(str, Enum):
    INTRO = "intro"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    FOLLOWUP = "followup"
    CLOSING = "closing"

# =========================================================
# VOICE IDS (FROM DASHBOARD)
# =========================================================
VOICE_IDS = {
    "primary": "JBFqnCBsd6RMkjVDRZzb",
    "alternate": "EXAVITQu4vr4xnSDxMaL",
}

# =========================================================
# VOICE TUNING
# =========================================================
def voice_settings(question_type: QuestionType, confidence: float):
    base = {
        QuestionType.INTRO:      {"stability": 0.55, "similarity_boost": 0.75, "style": 0.35},
        QuestionType.TECHNICAL:  {"stability": 0.65, "similarity_boost": 0.80, "style": 0.20},
        QuestionType.BEHAVIORAL: {"stability": 0.50, "similarity_boost": 0.70, "style": 0.45},
        QuestionType.FOLLOWUP:   {"stability": 0.70, "similarity_boost": 0.80, "style": 0.15},
        QuestionType.CLOSING:    {"stability": 0.45, "similarity_boost": 0.70, "style": 0.40},
    }[question_type]

    if confidence < 0.5:
        base["stability"] = max(0.0, base["stability"] - 0.05)
        base["style"] = min(1.0, base["style"] + 0.05)

    return base

# =========================================================
# TEXT SHAPING
# =========================================================
def shape_text(text: str, question_type: QuestionType) -> str:
    if question_type in (QuestionType.INTRO, QuestionType.BEHAVIORAL):
        return text.replace("?", "...?")
    return text

# =========================================================
# CORE FUNCTION: TEXT -> MP3 BYTES
# =========================================================
def synthesize_mp3(
    text: str,
    *,
    role: str = "primary",
    question_type: QuestionType = QuestionType.TECHNICAL,
    confidence: float = 0.7,
) -> bytes:
    """
    Returns raw MP3 bytes.
    Caller decides what to do with them (WS, file, mobile, etc.)
    """

    voice_id = VOICE_IDS.get(role, VOICE_IDS["primary"])
    text = shape_text(text, question_type)

    audio_stream = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
        voice_settings=voice_settings(question_type, confidence),
    )

    # ElevenLabs yields MP3 chunks -> concatenate
    mp3_bytes = b"".join(audio_stream)
    return mp3_bytes


# =========================================================
# OPENING / INTRO (FOR MOBILE PLAYBACK)
# =========================================================
def synthesize_opening_mp3(text: str) -> bytes:
    """
    Synthesize opening/intro text (e.g. from get_opening) to MP3 bytes.
    Use this to send audio to the mobile so the opening is heard on device.
    """
    return synthesize_mp3(
        text,
        role="primary",
        question_type=QuestionType.INTRO,
        confidence=0.7,
    )


def synthesize_question_mp3(text: str) -> bytes:
    """
    Synthesize LLM-generated question/follow-up text to MP3 bytes.
    Use this so every interviewer question is heard on the mobile, not just the opening.
    """
    return synthesize_mp3(
        text,
        role="primary",
        question_type=QuestionType.FOLLOWUP,
        confidence=0.7,
    )


def synthesize_closing_mp3(text: str) -> bytes:
    """
    Synthesize closing/thank-you text to MP3 bytes (heard on mobile when interview ends).
    """
    return synthesize_mp3(
        text,
        role="primary",
        question_type=QuestionType.CLOSING,
        confidence=0.7,
    )


# =========================================================
# DEMO (FILE WRITE ONLY)
# =========================================================
if __name__ == "__main__":
    audio = synthesize_mp3(
        "Can you explain how a hash map handles collisions?",
        role="primary",
        question_type=QuestionType.TECHNICAL,
        confidence=0.85,
    )

    with open("output.mp3", "wb") as f:
        f.write(audio)

    print("✅ MP3 written to output.mp3")