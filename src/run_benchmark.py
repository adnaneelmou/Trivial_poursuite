"""Run a resumable multiple-choice benchmark against LM Studio."""

import argparse
import csv
import json
import random
import re
import string
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from openai import OpenAI
from prompts import PROMPTS, render_prompt

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_FILE = ROOT / "silver/questions.parquet"
OUTPUT_FILE = ROOT / "bronze/ai_answers_raw.csv"

BASE_URL = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = "google/gemma-4-e4b"
DEFAULT_PROMPT_ID = "v1_letter_only"
MAX_TOKENS = 32

FIELDS = [
    "question_id",
    "model",
    "prompt_id",
    "prompt_text",
    "raw_output",
    "ai_answer",
    "expected_letter",
    "ai_correct",
    "follows_format",
    "is_unparsable",
    "response_time",
    "choices_order",
    "answered_at",
    "error",
]


def normalize_choice_text(value):
    """Normalize answer text so exact option text can be mapped back to a letter."""
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def parse_answer(raw_output, choices):
    """Return a choice letter and whether the output followed the letter-only format."""
    text = (raw_output or "").strip()
    valid_letters = [choice["letter"] for choice in choices]
    upper_text = text.upper()

    answer = ""
    answer_patterns = (
        r"\b(?:la\s+bonne\s+r[ée]ponse|bonne\s+r[ée]ponse|la\s+r[ée]ponse)"
        r"\s*(?:est|:|=)\s*[*`_]*([A-Z])\b",
        r"\b(?:the\s+correct\s+answer|the\s+answer)"
        r"\s*(?:is|:|=)\s*[*`_]*([A-Z])\b",
    )
    for pattern in answer_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match and match.group(1).upper() in valid_letters:
            answer = match.group(1).upper()
            break

    if not answer:
        match = re.match(r"^([A-Z])\b", upper_text)
        answer = match.group(1) if match and match.group(1) in valid_letters else ""

    if not answer:
        normalized_output = normalize_choice_text(text)
        matching_letters = [
            choice["letter"]
            for choice in choices
            if normalized_output == normalize_choice_text(choice["text"])
        ]
        if len(matching_letters) == 1:
            answer = matching_letters[0]

    follows_format = upper_text in valid_letters
    return answer, follows_format


def read_completed_keys():
    if not OUTPUT_FILE.exists():
        return set()
    with OUTPUT_FILE.open(encoding="utf-8", newline="") as csv_file:
        return {
            (row["question_id"], row["model"], row["prompt_id"])
            for row in csv.DictReader(csv_file)
        }


def append_result(row, write_header):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
        csv_file.flush()


def run(model, limit, prompt_id):
    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(
            f"Questions Parquet not found: {QUESTIONS_FILE}. "
            "Run src/prepare_silver.py first."
        )

    questions = pd.read_parquet(QUESTIONS_FILE)
    if limit is not None:
        questions = questions.head(limit)

    completed = read_completed_keys()
    needs_header = not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size == 0
    client = OpenAI(base_url=BASE_URL, api_key="lm-studio", timeout=180)
    added = 0

    for _, row in questions.iterrows():
        key = (str(row["question_id"]), model, prompt_id)
        if key in completed:
            continue

        options = list(row["answer_options"])
        # Use a local seeded RNG so every model sees the same order per question.
        random.Random(str(row["question_id"])).shuffle(options)
        letters = list(string.ascii_uppercase[: len(options)])
        choices = [
            {"letter": letter, "text": str(option)}
            for letter, option in zip(letters, options)
        ]
        expected_letter = next(
            letter
            for letter, option in zip(letters, options)
            if str(option) == str(row["correct_answer"])
        )
        prompt_text = render_prompt(prompt_id, str(row["question"]), choices)
        started = time.perf_counter()
        raw_output = ""
        error = ""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0,
                max_tokens=MAX_TOKENS,
                extra_body={"reasoning_effort": "none"},
            )
            raw_output = response.choices[0].message.content or ""
        except Exception as exc:
            error = str(exc)
        response_time = time.perf_counter() - started

        ai_answer, follows_format = parse_answer(raw_output, choices)
        is_unparsable = not bool(ai_answer) and not bool(error)
        ai_correct = (
            ai_answer == expected_letter if ai_answer else ""
        )
        result = {
            "question_id": key[0],
            "model": model,
            "prompt_id": prompt_id,
            "prompt_text": prompt_text,
            "raw_output": raw_output,
            "ai_answer": ai_answer,
            "expected_letter": expected_letter,
            "ai_correct": ai_correct,
            "follows_format": follows_format,
            "is_unparsable": is_unparsable,
            "response_time": round(response_time, 4),
            "choices_order": json.dumps(choices, ensure_ascii=False),
            "answered_at": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }
        append_result(result, needs_header)
        needs_header = False
        completed.add(key)
        added += 1
        print(
            f"{added}: {row['question_id']} | answer={ai_answer or 'unparsable'} "
            f"| expected={expected_letter} | correct={ai_correct} "
            f"| {response_time:.2f}s",
            flush=True,
        )

    print(f"Added {added} result(s) to {OUTPUT_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark an LM Studio model against OpenTDB questions."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--prompt",
        choices=sorted(PROMPTS),
        default=DEFAULT_PROMPT_ID,
        help="Prompt version to use (default: v1_letter_only).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Number of questions to process (default: 1).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every question in Silver.",
    )
    args = parser.parse_args()
    if args.limit < 1 and not args.all:
        parser.error("--limit must be at least 1")
    run(args.model, None if args.all else args.limit, args.prompt)


if __name__ == "__main__":
    main()
