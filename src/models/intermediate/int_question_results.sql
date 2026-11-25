select
    *,
    case
        when ai_correct is true then 1.0
        when ai_correct is false then 0.0
        else null
    end as correctness_score,
    case
        when array_length(answer_options) > 0
            then 1.0 / array_length(answer_options)
        else null
    end as random_baseline,
    length(question) as question_length,
    case when error is null or error = '' then false else true end as has_runtime_error,
    case
        when error is not null and error <> '' then 'runtime_error'
        when is_unparsable is true then 'unparsable'
        when ai_correct is true then 'correct'
        else 'incorrect'
    end as answer_status,
    case ai_answer
        when 'A' then 1 when 'B' then 2 when 'C' then 3 when 'D' then 4
        else null
    end as selected_position,
    case expected_letter
        when 'A' then 1 when 'B' then 2 when 'C' then 3 when 'D' then 4
        else null
    end as expected_position
from {{ ref('stg_benchmark') }}
