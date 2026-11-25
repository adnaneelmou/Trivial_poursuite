"""Reconcile Bronze question counts against OpenTDB's verified counts."""

import csv
import hashlib
import html
import json
import time
from collections import Counter
from pathlib import Path

import requests

API = "https://opentdb.com"
OUTPUT = Path(__file__).resolve().parents[1] / "bronze/questions_raw.csv"
FIELDS = [
    "question_id", "category", "type", "difficulty", "question",
    "correct_answer", "incorrect_answers",
]


def api_get(url, params=None):
    while True:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 429:
            print("Rate limit reached; waiting 5 seconds.", flush=True)
            time.sleep(5.2)
            continue
        response.raise_for_status()
        return response.json()


def read_questions():
    if not OUTPUT.exists():
        return {}
    with OUTPUT.open(encoding="utf-8", newline="") as file:
        rows = {}
        for row in csv.DictReader(file):
            row["incorrect_answers"] = json.loads(row["incorrect_answers"])
            rows[row["question_id"]] = row
        return rows


def save_questions(rows):
    with OUTPUT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows.values():
            item = row.copy()
            item["incorrect_answers"] = json.dumps(
                item["incorrect_answers"], ensure_ascii=False
            )
            writer.writerow(item)


def make_row(item):
    row = {
        key: html.unescape(value) if isinstance(value, str) else value
        for key, value in item.items()
    }
    content = {key: row[key] for key in FIELDS if key != "question_id"}
    stable = json.dumps(
        content, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    row["question_id"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()
    return row


def main():
    rows = read_questions()
    global_counts = api_get(f"{API}/api_count_global.php")
    category_list = api_get(f"{API}/api_category.php")["trivia_categories"]
    expected = global_counts["categories"]
    token = api_get(
        f"{API}/api_token.php", {"command": "request"}
    )["token"]
    local_counts = Counter(row["category"] for row in rows.values())

    for category in category_list:
        category_id = str(category["id"])
        category_name = category["name"]
        target = expected.get(category_id, {}).get(
            "total_num_of_verified_questions", 0
        )
        if local_counts[category_name] >= target:
            continue

        print(
            f"Reconciling {category_name}: {local_counts[category_name]}/{target}",
            flush=True,
        )
        fetched_with_token = 0
        token_restarts = 0
        while local_counts[category_name] < target:
            remaining = target - fetched_with_token
            amount = min(50, max(1, remaining))
            result = api_get(
                f"{API}/api.php",
                {"amount": amount, "category": category_id, "token": token},
            )
            code = result["response_code"]

            if code in (1, 4):
                if amount > 1:
                    # A session can reject a final request larger than its remainder.
                    fetched_with_token = target - max(
                        0, target - fetched_with_token
                    )
                    reduced = max(1, amount // 2)
                    print(f"Response code {code}; reducing request to {reduced}.")
                    # Track the reduced size for the retry without advancing the token.
                    amount = reduced
                    while True:
                        result = api_get(
                            f"{API}/api.php",
                            {"amount": amount, "category": category_id, "token": token},
                        )
                        code = result["response_code"]
                        if code == 0:
                            break
                        if code == 3:
                            token = api_get(
                                f"{API}/api_token.php", {"command": "request"}
                            )["token"]
                            fetched_with_token = 0
                            break
                        if amount == 1:
                            code = 4
                            break
                        amount = max(1, amount // 2)
                    if code == 0:
                        pass
                    elif code == 3:
                        continue
                    else:
                        token_restarts += 1
                        if token_restarts > 5:
                            raise RuntimeError(
                                f"Could not complete {category_name} after 5 tokens"
                            )
                        token = api_get(
                            f"{API}/api_token.php", {"command": "request"}
                        )["token"]
                        fetched_with_token = 0
                        continue
                else:
                    token_restarts += 1
                    if token_restarts > 5:
                        raise RuntimeError(
                            f"Could not complete {category_name} after 5 tokens"
                        )
                    token = api_get(
                        f"{API}/api_token.php", {"command": "request"}
                    )["token"]
                    fetched_with_token = 0
                    continue

            if code == 3:
                token = api_get(
                    f"{API}/api_token.php", {"command": "request"}
                )["token"]
                fetched_with_token = 0
                continue
            if code != 0:
                raise RuntimeError(f"OpenTDB response_code={code}")

            results = result.get("results", [])
            if not results:
                raise RuntimeError(f"Empty result page for {category_name}")
            fetched_with_token += len(results)
            for item in results:
                row = make_row(item)
                rows[row["question_id"]] = row
            local_counts = Counter(row["category"] for row in rows.values())
            save_questions(rows)
            print(
                f"{category_name}: {local_counts[category_name]}/{target} unique",
                flush=True,
            )
            time.sleep(5.2)

    total_target = global_counts["overall"]["total_num_of_verified_questions"]
    print(f"Reconciled {len(rows)}/{total_target} unique verified questions.")


if __name__ == "__main__":
    main()
