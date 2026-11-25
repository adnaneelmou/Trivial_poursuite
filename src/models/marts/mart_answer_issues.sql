select
    question_id,
    model,
    prompt_id,
    category,
    difficulty,
    question_type,
    question,
    answer_options,
    choices_order,
    correct_answer,
    expected_letter,
    ai_answer,
    raw_output,
    answer_status,
    follows_format,
    response_time,
    error
from {{ ref('int_question_results') }}
where answer_status in ('incorrect', 'unparsable', 'runtime_error')
