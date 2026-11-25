"""Normalize the raw OpenTDB CSV and write a typed Parquet dataset."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BRONZE_FILE = ROOT / "bronze/questions_raw.csv"
SILVER_FILE = ROOT / "silver/questions.parquet"


def parse_incorrect_answers(value):
    answers = json.loads(value)
    if not isinstance(answers, list):
        raise ValueError("incorrect_answers must contain a JSON list")
    return [str(answer).strip() for answer in answers]


def main():
    if not BRONZE_FILE.exists():
        raise FileNotFoundError(f"Missing Bronze input: {BRONZE_FILE}")

    raw = pd.read_csv(BRONZE_FILE, dtype=str, keep_default_na=False)
    required = {
        "question_id", "category", "type", "difficulty", "question",
        "correct_answer", "incorrect_answers",
    }
    missing_columns = required - set(raw.columns)
    if missing_columns:
        raise ValueError(f"Missing columns in Bronze CSV: {sorted(missing_columns)}")

    clean = pd.DataFrame(
        {
            "question_id": raw["question_id"].str.strip(),
            "category": raw["category"].str.strip(),
            "question_type": raw["type"].str.strip().str.lower(),
            "difficulty": raw["difficulty"].str.strip().str.lower(),
            "question": raw["question"].str.strip(),
            "correct_answer": raw["correct_answer"].str.strip(),
            "incorrect_answers": raw["incorrect_answers"].map(parse_incorrect_answers),
        }
    )
    clean["answer_options"] = clean.apply(
        lambda row: [row["correct_answer"], *row["incorrect_answers"]], axis=1
    )

    if clean[list(required - {"type", "incorrect_answers"})].eq("").any().any():
        raise ValueError("Found empty values in required question fields")
    if clean["question_id"].duplicated().any():
        raise ValueError("Found duplicate question_id values in Bronze")

    SILVER_FILE.parent.mkdir(parents=True, exist_ok=True)
    clean.to_parquet(SILVER_FILE, index=False, engine="pyarrow")
    print(f"Silver written: {len(clean):,} rows -> {SILVER_FILE}")
    print(f"Categories: {clean['category'].nunique()}; difficulties: "
          f"{', '.join(sorted(clean['difficulty'].unique()))}")


if __name__ == "__main__":
    main()
