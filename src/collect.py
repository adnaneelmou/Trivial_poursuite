"""Collect all questions exposed by OpenTDB's session-token API."""

import csv
import hashlib
import html
import json
import hashlib
import time
from pathlib import Path

import requests

API = "https://opentdb.com"
OUTPUT = Path("bronze/questions_raw.csv")
FIELDS = [
    "question_id",
    "category",
    "type",
    "difficulty",
    "question",
    "correct_answer",
    "incorrect_answers",
]


def question_id(question):
    content = {key: question[key] for key in FIELDS if key != "question_id"}
    stable = json.dumps(
        content, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def api_get(url, params=None):
    """Call OpenTDB and retry when its per-IP rate limit is reached."""
    while True:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 429:
            print("Rate limit reached; waiting 5 seconds.", flush=True)
            time.sleep(5.2)
            continue
        response.raise_for_status()
        return response.json()


def save_questions(questions):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        writer.writeheader()
        for question in questions.values():
            row = question.copy()
            row["incorrect_answers"] = json.dumps(
                row["incorrect_answers"], ensure_ascii=False
            )
            writer.writerow(row)


def main():
    questions = {}
    if OUTPUT.exists():
        with OUTPUT.open(encoding="utf-8", newline="") as csv_file:
            for row in csv.DictReader(csv_file):
                row["incorrect_answers"] = json.loads(row["incorrect_answers"])
                row["question_id"] = question_id(row)
                questions[row["question_id"]] = row

    counts = api_get(f"{API}/api_count_global.php")
    target = counts["overall"]["total_num_of_verified_questions"]
    print(f"Already collected: {len(questions)}; verified target: {target}")

    def new_token():
        token_result = api_get(
            f"{API}/api_token.php", {"command": "request"}
        )
        return token_result["token"]

    token = new_token()
    amount = 50
    token_resets = 0

    while len(questions) < target:
        result = api_get(
            f"{API}/api.php", {"amount": amount, "token": token}
        )
        response_code = result["response_code"]

        if response_code in (1, 4):
            if amount > 1:
                amount = max(1, amount // 2)
                print(f"Token returned code {response_code}; retrying with amount={amount}.")
                continue
            token_resets += 1
            if token_resets > 5:
                raise RuntimeError(
                    f"Reached {token_resets} exhausted tokens at {len(questions)}/{target} questions."
                )
            print(f"Token exhausted at amount=1; requesting token {token_resets + 1}.")
            token = new_token()
            amount = 50
            continue
        if response_code == 3:
            print("Session token expired; requesting a new one.")
            token = new_token()
            amount = 50
            continue
        if response_code != 0:
            raise RuntimeError(
                f"Unexpected OpenTDB response code: {response_code}"
            )

        for item in result["results"]:
            question = {
                key: html.unescape(value) if isinstance(value, str) else value
                for key, value in item.items()
            }
            question["question_id"] = question_id(question)
            questions[question["question_id"]] = question

        # Save each page so collected data survives an interruption.
        save_questions(questions)
        print(f"Saved {len(questions)}/{target} unique verified questions.", flush=True)
        amount = 50
        time.sleep(5.2)

    save_questions(questions)
    print(f"Collection complete: {len(questions)} verified questions in {OUTPUT}")


if __name__ == "__main__":
    main()
