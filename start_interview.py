import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ======================================================
# USER INPUT
# ======================================================
ROLE = input("Enter role (e.g., Software Engineer): ").strip()

DIFFICULTY = input("Enter difficulty (easy / medium / hard): ").strip().upper()
assert DIFFICULTY in {"EASY", "MEDIUM", "HARD"}, \
    "Difficulty must be easy, medium, or hard"

# ======================================================
# LOAD PROMPT FILES
# ======================================================
with open("interview_prompt.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()

with open("resume_text.md", "r", encoding="utf-8") as f:
    RESUME_TEXT = f.read()

SYSTEM_PROMPT = (
    SYSTEM_PROMPT_TEMPLATE
    .replace("{ROLE}", ROLE)
    .replace("{DIFFICULTY}", DIFFICULTY)
)

# ======================================================
# GPU ASSERTION
# ======================================================
assert torch.cuda.is_available(), "❌ GPU not available. Enable GPU in Colab."
device = torch.device("cuda")

# ======================================================
# MODEL CONFIG
# ======================================================
MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"
DTYPE = torch.float16

MAX_NEW_TOKENS = 120
TEMPERATURE = 0.15
DO_SAMPLE = True
REPETITION_PENALTY = 1.1

# ======================================================
# LOAD TOKENIZER
# ======================================================
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token

# ======================================================
# LOAD MODEL
# ======================================================
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=DTYPE,
    device_map="cuda"
)
model.eval()

print("✅ LLaMA 3.2 3B Instruct loaded on GPU")

# ======================================================
# CHAT STATE
# ======================================================
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "system",
        "content": (
            "Background resume context (read-only). "
            "Do not quote or repeat unless explicitly allowed:\n"
            f"<<<<\n{RESUME_TEXT}\n>>>>"
        )
    }
]

# ======================================================
# GENERATION FUNCTION
# ======================================================
def generate_interviewer_question(messages):
    enc = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True
    ).to(device)

    input_ids = enc["input_ids"]

    with torch.no_grad():
        output = model.generate(
            input_ids=input_ids,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=DO_SAMPLE,
            repetition_penalty=REPETITION_PENALTY,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = output[0][input_ids.shape[-1]:]
    decoded = tokenizer.decode(generated, skip_special_tokens=True).strip()

    # Hard cleanup
    for bad in ["Candidate:", "candidate:", "please respond", "respond as"]:
        decoded = decoded.replace(bad, "")

    return decoded.strip()

# ======================================================
# START INTERVIEW
# ======================================================
print("\n🎤 Interview started\n")

question = generate_interviewer_question(messages)
print(f"Interviewer: {question}")

while True:
    user_input = input("\nCandidate: ").strip()

    if user_input.lower() in {"exit", "quit"}:
        print("\nInterview ended.")
        break

    messages.append({
        "role": "user",
        "content": f"Candidate response: {user_input}"
    })

    question = generate_interviewer_question(messages)
    print(f"\nInterviewer: {question}")
