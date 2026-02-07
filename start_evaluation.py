"""
Interview log evaluator: run via CLI or call run_evaluation(log_path) from server.
"""
import argparse
import json
import re
from pathlib import Path
from llama_cpp import Llama

_SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_PATH = str(_SCRIPT_DIR / "models" / "Llama-3.2-3B-Instruct-Q4_K_M.gguf")
EVALUATOR_PROMPT_PATH = _SCRIPT_DIR / "evaluator.md"
EVALUATIONS_DIR = _SCRIPT_DIR / "evaluations"


def _extract_json(text: str) -> dict:
    """Extract the first valid JSON object from model output."""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in evaluator output.")
    return json.loads(match.group(0))


def run_evaluation(log_path: Path) -> dict:
    """
    Load interview log, run LLM evaluation, save result to evaluations/, return result.
    Can be called from server after interview completes (e.g. in a thread or executor).
    """
    log_path = Path(log_path).resolve()
    if not log_path.exists():
        raise FileNotFoundError(f"Interview log not found: {log_path}")

    if not EVALUATOR_PROMPT_PATH.exists():
        raise FileNotFoundError("evaluator.md not found")

    interview_data = json.loads(log_path.read_text(encoding="utf-8"))
    evaluator_prompt = EVALUATOR_PROMPT_PATH.read_text(encoding="utf-8")

    qa_pairs = interview_data.get("qa_pairs", [])
    metadata = interview_data.get("metadata", {})
    role = metadata.get("role", "Software Engineer")
    difficulty = str(metadata.get("difficulty", "MEDIUM")).lower()

    transcript_lines = []
    for pair in qa_pairs:
        q, a = pair.get("question", ""), pair.get("answer", "")
        transcript_lines.append(f"Interviewer: {q}")
        transcript_lines.append(f"Candidate: {a}")
    full_transcript = "\n".join(transcript_lines)

    evaluation_input = {
        "role": role,
        "difficulty": difficulty,
        "interview_transcript": full_transcript,
    }

    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=8192,
        n_threads=8,
        n_batch=512,
        n_gpu_layers=-1,
        temperature=0.0,
        verbose=False,
    )

    eval_messages = [
        {"role": "system", "content": evaluator_prompt},
        {"role": "user", "content": json.dumps(evaluation_input, indent=2)},
    ]
    eval_output = llm.create_chat_completion(
        messages=eval_messages,
        max_tokens=2000,
        stop=["<|eot_id|>"],
    )["choices"][0]["message"]["content"]

    evaluation_result = _extract_json(eval_output)

    EVALUATIONS_DIR.mkdir(exist_ok=True)
    output_path = EVALUATIONS_DIR / f"{log_path.stem}.evaluation.json"
    output_path.write_text(
        json.dumps(evaluation_result, indent=2),
        encoding="utf-8",
    )
    return evaluation_result


# ======================================================
# CLI
# ======================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate an interview log (local file)."
    )
    parser.add_argument(
        "log_file",
        type=Path,
        help="Path to the interview log JSON (e.g. logs/interview_log_20260207_053019.json)",
    )
    args = parser.parse_args()
    log_path = args.log_file.resolve()
    if not log_path.exists():
        raise SystemExit(f"❌ Interview log file not found at {log_path}")
    print("✅ GGUF evaluator loading...")
    result = run_evaluation(log_path)
    print(f"✅ Evaluation saved to {EVALUATIONS_DIR / log_path.stem}.evaluation.json")
    print(json.dumps(result, indent=2))
