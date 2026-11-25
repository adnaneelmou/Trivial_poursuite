{{ config(materialized='view') }}

select
    question_id,
    model,
    prompt_id,
    prompt_text,
    raw_output,
    ai_answer,
    expected_letter,
    try_cast(ai_correct as boolean) as ai_correct,
    try_cast(follows_format as boolean) as follows_format,
    try_cast(is_unparsable as boolean) as is_unparsable,
    try_cast(response_time as double) as response_time,
    try_cast(answered_at as timestamptz) as answered_at,
    category,
    split_part(category, ':', 1) as category_group,
    question_type,
    difficulty,
    question,
    correct_answer,
    answer_options,
    choices_order,
    error,
    question_id || '|' || model || '|' || prompt_id as observation_id
from read_parquet('silver/obt_answers.parquet')
