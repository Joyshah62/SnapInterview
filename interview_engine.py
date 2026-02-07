import os
from llama_cpp import Llama

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "Llama-3.2-3B-Instruct-Q4_K_M.gguf")

_llm = None


def _ensure_model():
    global _llm
    if _llm is not None:
        return
    _llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=8,
        n_gpu_layers=0,
        temperature=0.15,
        repeat_penalty=1.1,
        verbose=False,
    )


def get_opening(role: str) -> str:
    return (
        f"Hi, I'm SnapAI, and I'll be interviewing you for the {role} position. "
        "Could you briefly introduce yourself?"
    )


def create_interview_session(role: str, difficulty: str) -> dict:
    with open(os.path.join(SCRIPT_DIR, "interview_prompt.md"), "r", encoding="utf-8") as f:
        system_prompt_template = f.read()
    resume_path = os.path.join(SCRIPT_DIR, "resume_text.md")
    resume_text = ""
    if os.path.exists(resume_path):
        with open(resume_path, "r", encoding="utf-8") as f:
            resume_text = f.read()
    system_prompt = (
        system_prompt_template
        .replace("{ROLE}", role)
        .replace("{DIFFICULTY}", difficulty)
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "system",
            "content": (
                "Background resume context (read-only).\n"
                f"<<<<\n{resume_text}\n>>>>"
            ),
        },
    ]
    return {"messages": messages}


def generate_question(session: dict) -> str:
    _ensure_model()
    messages = session["messages"].copy()
    output = _llm.create_chat_completion(
        messages=messages,
        max_tokens=120,
        temperature=0.15,
        repeat_penalty=1.1,
    )
    text = output["choices"][0]["message"]["content"].strip()
    for bad in ["Candidate:", "candidate:"]:
        text = text.replace(bad, "")
    return text.strip()


def add_response_and_generate(session: dict, candidate_text: str) -> str:
    session["messages"].append(
        {"role": "user", "content": f"Candidate response: {candidate_text}"}
    )
    return generate_question(session)


def add_response(session: dict, candidate_text: str):
    session["messages"].append(
        {"role": "user", "content": f"Candidate response: {candidate_text}"}
    )


def transcribe_audio(wav_path: str) -> str:
    try:
        from transformers import pipeline
        pipe = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")
        result = pipe(wav_path)
        if isinstance(result, dict) and "text" in result:
            return result["text"].strip()
        if isinstance(result, list) and result and isinstance(result[0], dict) and "text" in result[0]:
            return result[0]["text"].strip()
        return str(result).strip() if result else ""
    except Exception:
        return ""
