select
    model,
    prompt_id,
    difficulty,
    question_type,
    count(*) as observations,
    avg(correctness_score) as accuracy,
    avg(random_baseline) as random_baseline,
    avg(correctness_score) - avg(random_baseline) as accuracy_vs_random,
    avg(response_time) as avg_response_time
from {{ ref('int_question_results') }}
group by model, prompt_id, difficulty, question_type
