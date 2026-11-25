"""Join OpenTDB questions and raw model answers into one Silver Parquet table."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_FILE = ROOT / "bronze/questions_raw.csv"
ANSWERS_FILE = ROOT / "bronze/ai_answers_raw.csv"
OUTPUT_FILE = ROOT / "silver/obt_answers.parquet"


def main():
    for path in (QUESTIONS_FILE, ANSWERS_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Required Bronze input not found: {path}")

    questions = pd.read_csv(QUESTIONS_FILE, dtype=str, keep_default_na=False)
    answers = pd.read_csv(ANSWERS_FILE, dtype=str, keep_default_na=False)

    if questions["question_id"].duplicated().any():
        raise ValueError("Bronze questions contains duplicate question_id values")
    if answers.duplicated(["question_id", "model", "prompt_id"]).any():
        raise ValueError("Bronze answers contains duplicate benchmark observations")

    question_ids = set(questions["question_id"])
    orphan_ids = set(answers["question_id"]) - question_ids
    if orphan_ids:
        raise ValueError(
            f"{len(orphan_ids)} answer question_id values do not exist in Bronze questions"
        )

    questions["incorrect_answers"] = questions["incorrect_answers"].map(json.loads)
    questions["answer_options"] = questions.apply(
        lambda row: [row["correct_answer"], *row["incorrect_answers"]], axis=1
    )
    questions["question_type"] = questions.pop("type").str.lower()
    questions["difficulty"] = questions["difficulty"].str.lower()
    questions["category_group"] = questions["category"].str.split(":", n=1).str[0].str.strip()

    silver = answers.merge(
        questions,
        on="question_id",
        how="left",
        validate="many_to_one",
    )
    for column in ("ai_correct", "follows_format", "is_unparsable"):
        silver[column] = silver[column].map(
            {"True": True, "False": False, "": None}
        ).astype("boolean")
    silver["response_time"] = pd.to_numeric(
        silver["response_time"], errors="coerce"
    )
    silver["answered_at"] = pd.to_datetime(
        silver["answered_at"], utc=True, errors="coerce"
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(OUTPUT_FILE, index=False, engine="pyarrow")
    print(
        f"Silver written: {len(silver):,} benchmark observations -> {OUTPUT_FILE}"
    )
    print(
        f"Questions joined: {silver['question_id'].nunique():,}; "
        f"models: {silver['model'].nunique()}; prompts: {silver['prompt_id'].nunique()}"
    )


if __name__ == "__main__":
    main()
