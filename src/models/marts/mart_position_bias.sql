with position_counts as (
    select
        model,
        prompt_id,
        selected_position,
        count(*) as selections,
        avg(correctness_score) as accuracy_when_selected
    from {{ ref('int_question_results') }}
    where selected_position is not null
    group by model, prompt_id, selected_position
)
select
    *,
    selections * 1.0 / sum(selections) over (partition by model, prompt_id) as selection_rate
from position_counts
