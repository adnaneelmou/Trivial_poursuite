select
    model,
    prompt_id,
    count(*) as observations,
    countif(ai_correct is not null) as scored_observations,
    avg(correctness_score) as accuracy,
    avg(random_baseline) as random_baseline,
    avg(correctness_score) - avg(random_baseline) as accuracy_vs_random,
    avg(cast(follows_format as integer)) as format_rate,
    avg(cast(is_unparsable as integer)) as unparsable_rate,
    avg(cast(has_runtime_error as integer)) as runtime_error_rate,
    avg(response_time) as avg_response_time,
    quantile_cont(response_time, 0.5) as median_response_time,
    quantile_cont(response_time, 0.95) as p95_response_time
from {{ ref('int_question_results') }}
group by model, prompt_id
