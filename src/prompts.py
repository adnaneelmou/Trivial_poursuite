"""Versioned prompt templates used by the local benchmark."""

PROMPTS = {
    # Keep this wording and ID stable: existing Bronze rows use this prompt.
    "v1_letter_only": {
        "label": "Consigne stricte",
        "instruction": (
            "Réponds uniquement par la lettre correspondant à la bonne réponse. "
            "N'ajoute ni explication ni ponctuation."
        ),
    },
    "v2_simple": {
        "label": "Consigne simple",
        "instruction": "Quelle est la bonne réponse ?",
    },
}


def render_prompt(prompt_id, question, choices):
    """Build a prompt while keeping the question and option layout consistent."""
    if prompt_id not in PROMPTS:
        valid_ids = ", ".join(PROMPTS)
        raise ValueError(f"Unknown prompt_id {prompt_id!r}. Choose from: {valid_ids}")

    choice_lines = "\n".join(
        f"{choice['letter']}. {choice['text']}" for choice in choices
    )
    question_block = f"Question : {question}\nChoix :\n{choice_lines}"
    instruction = PROMPTS[prompt_id]["instruction"]

    if prompt_id == "v1_letter_only":
        # Preserve the exact format used by the existing benchmark rows.
        return f"{instruction}\n\n{question_block}"
    return f"{question_block}\n\n{instruction}"
