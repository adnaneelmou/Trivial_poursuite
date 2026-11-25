from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "gold/benchmark.duckdb"

st.set_page_config(
    page_title="Benchmark Trivial Poursuite",
    page_icon="🎯",
    layout="wide",
)
st.title("Benchmark de culture générale")
st.caption(
    "Comparaison des réponses du modèle aux réponses de référence OpenTDB. "
    "La précision est calculée sur les réponses analysables."
)

if not DATABASE.exists():
    st.error("La base Gold est absente. Lance d’abord les transformations dbt.")
    st.stop()

try:
    connection = duckdb.connect(str(DATABASE), read_only=True)
    detail = connection.execute(
        """
        select b.*, i.random_baseline, i.correctness_score, i.has_runtime_error,
               i.answer_status, i.selected_position, i.expected_position
        from staging.stg_benchmark as b
        join intermediate.int_question_results as i using (observation_id)
        """
    ).df()
    model_mart = connection.execute(
        "select * from marts.mart_model_prompt"
    ).df()
    category_mart = connection.execute(
        "select * from marts.mart_category_performance"
    ).df()
    difficulty_mart = connection.execute(
        "select * from marts.mart_difficulty_performance"
    ).df()
    position_mart = connection.execute(
        "select * from marts.mart_position_bias"
    ).df()
    issues_mart = connection.execute(
        "select * from marts.mart_answer_issues"
    ).df()
    connection.close()
except Exception as error:
    st.error(f"Impossible de lire les tables DuckDB : {error}")
    st.stop()

if detail.empty:
    st.info("Aucune observation disponible dans Gold.")
    st.stop()

with st.sidebar:
    st.header("Filtres")
    selected_models = st.multiselect(
        "Modèle", sorted(detail["model"].dropna().unique()),
        default=sorted(detail["model"].dropna().unique()),
    )
    selected_prompts = st.multiselect(
        "Prompt", sorted(detail["prompt_id"].dropna().unique()),
        default=sorted(detail["prompt_id"].dropna().unique()),
    )
    selected_categories = st.multiselect(
        "Catégorie", sorted(detail["category"].dropna().unique()),
        default=sorted(detail["category"].dropna().unique()),
    )
    selected_difficulties = st.multiselect(
        "Difficulté", sorted(detail["difficulty"].dropna().unique()),
        default=sorted(detail["difficulty"].dropna().unique()),
    )
    selected_types = st.multiselect(
        "Type de question", sorted(detail["question_type"].dropna().unique()),
        default=sorted(detail["question_type"].dropna().unique()),
    )

filtered = detail[
    detail["model"].isin(selected_models)
    & detail["prompt_id"].isin(selected_prompts)
    & detail["category"].isin(selected_categories)
    & detail["difficulty"].isin(selected_difficulties)
    & detail["question_type"].isin(selected_types)
].copy()
all_topics = (
    len(selected_categories) == detail["category"].nunique()
    and len(selected_difficulties) == detail["difficulty"].nunique()
    and len(selected_types) == detail["question_type"].nunique()
)

if filtered.empty:
    st.warning("Aucune observation ne correspond à ces filtres.")
    st.stop()

accuracy = filtered["ai_correct"].mean()
baseline = filtered["random_baseline"].mean()
format_rate = filtered["follows_format"].mean()
median_latency = filtered["response_time"].median()
p95_latency = filtered["response_time"].quantile(0.95)
scored = int(filtered["ai_correct"].notna().sum())
unparsable = int(filtered["is_unparsable"].fillna(False).sum())
runtime_errors = int(filtered["has_runtime_error"].fillna(False).sum())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Précision", f"{accuracy:.1%}" if pd.notna(accuracy) else "—")
k2.metric("Baseline aléatoire", f"{baseline:.1%}" if pd.notna(baseline) else "—")
k3.metric("Réponses notées", f"{scored:,} / {len(filtered):,}")
k4.metric("Latence médiane", f"{median_latency:.2f} s")
k5.metric("Latence p95", f"{p95_latency:.2f} s")
st.caption(
    f"Respect du format : {format_rate:.1%} · Réponses non analysables : "
    f"{unparsable} · Erreurs runtime : {runtime_errors}"
)

overview_tab, topics_tab, latency_tab, answers_tab = st.tabs(
    ["Vue générale", "Catégories et difficulté", "Temps et robustesse", "Réponses à examiner"]
)

with overview_tab:
    st.subheader("Modèle et prompt")
    # Use the Gold mart for the unfiltered model/prompt ranking. When thematic
    # filters are active, aggregate the filtered observation grain instead.
    if all_topics:
        ranking = model_mart[
            model_mart["model"].isin(selected_models)
            & model_mart["prompt_id"].isin(selected_prompts)
        ].copy()
    else:
        ranking = filtered.groupby(["model", "prompt_id"], as_index=False).agg(
            accuracy=("correctness_score", "mean"),
            random_baseline=("random_baseline", "mean"),
            observations=("question_id", "size"),
            scored_observations=("ai_correct", "count"),
            format_rate=("follows_format", "mean"),
            median_response_time=("response_time", "median"),
            p95_response_time=("response_time", lambda s: s.quantile(0.95)),
        )
        ranking["accuracy_vs_random"] = ranking["accuracy"] - ranking["random_baseline"]
    if not ranking.empty:
        metrics = ranking.melt(
            id_vars=["model", "prompt_id"],
            value_vars=["accuracy", "random_baseline"],
            var_name="metric",
            value_name="rate",
        )
        metrics["metric"] = metrics["metric"].map(
            {"accuracy": "Précision", "random_baseline": "Hasard"}
        )
        st.plotly_chart(
            px.bar(
                metrics,
                x="model",
                y="rate",
                color="metric",
                barmode="group",
                facet_col="prompt_id",
                range_y=[0, 1],
                labels={"rate": "Taux", "model": "Modèle", "prompt_id": "Prompt"},
            ),
            width="stretch",
        )
        table_cols = [
            "model", "prompt_id", "observations", "scored_observations",
            "accuracy", "random_baseline", "accuracy_vs_random", "format_rate",
            "median_response_time", "p95_response_time",
        ]
        st.dataframe(ranking[table_cols], width="stretch", hide_index=True)
    else:
        st.info("Aucun résultat modèle/prompt pour cette sélection.")

with topics_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Précision par catégorie")
        category_is_unfiltered = (
            len(selected_difficulties) == detail["difficulty"].nunique()
            and len(selected_types) == detail["question_type"].nunique()
        )
        if category_is_unfiltered:
            categories = category_mart[
                category_mart["model"].isin(selected_models)
                & category_mart["prompt_id"].isin(selected_prompts)
                & category_mart["category"].isin(selected_categories)
            ].copy()
        else:
            categories = filtered.groupby(
                ["model", "prompt_id", "category"], as_index=False
            ).agg(
                accuracy=("correctness_score", "mean"),
                random_baseline=("random_baseline", "mean"),
                observations=("question_id", "size"),
            )
        if not categories.empty:
            st.plotly_chart(
                px.bar(
                    categories,
                    x="category",
                    y="accuracy",
                    color="model",
                    barmode="group",
                    range_y=[0, 1],
                    hover_data=["observations", "random_baseline", "accuracy_vs_random"],
                    labels={"accuracy": "Précision", "category": "Catégorie"},
                ),
                width="stretch",
            )
    with right:
        st.subheader("Difficulté et type")
        difficulty_is_unfiltered = (
            len(selected_categories) == detail["category"].nunique()
        )
        if difficulty_is_unfiltered:
            difficulties = difficulty_mart[
                difficulty_mart["model"].isin(selected_models)
                & difficulty_mart["prompt_id"].isin(selected_prompts)
                & difficulty_mart["difficulty"].isin(selected_difficulties)
                & difficulty_mart["question_type"].isin(selected_types)
            ].copy()
        else:
            difficulties = filtered.groupby(
                ["model", "prompt_id", "difficulty", "question_type"],
                as_index=False,
            ).agg(
                accuracy=("correctness_score", "mean"),
                random_baseline=("random_baseline", "mean"),
                observations=("question_id", "size"),
            )
        if not difficulties.empty:
            st.plotly_chart(
                px.bar(
                    difficulties,
                    x="difficulty",
                    y="accuracy",
                    color="model",
                    barmode="group",
                    facet_col="question_type",
                    range_y=[0, 1],
                    hover_data=["observations", "random_baseline", "accuracy_vs_random"],
                    labels={"accuracy": "Précision", "difficulty": "Difficulté"},
                ),
                width="stretch",
            )

with latency_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Distribution des temps de réponse")
        st.plotly_chart(
            px.box(
                filtered,
                x="model",
                y="response_time",
                color="model",
                points="outliers",
                labels={"response_time": "Secondes", "model": "Modèle"},
            ),
            width="stretch",
        )
    with right:
        st.subheader("Format et robustesse")
        robustness = filtered.groupby("model", as_index=False).agg(
            follows_format=("follows_format", "mean"),
            unparsable_rate=("is_unparsable", "mean"),
            runtime_error_rate=("has_runtime_error", "mean"),
        )
        st.dataframe(robustness, width="stretch", hide_index=True)

    st.subheader("Préférence de position de réponse")
    if all_topics:
        positions = position_mart[
            position_mart["model"].isin(selected_models)
            & position_mart["prompt_id"].isin(selected_prompts)
        ].copy()
    else:
        positions = filtered.dropna(subset=["selected_position"]).groupby(
            ["model", "prompt_id", "selected_position"], as_index=False
        ).agg(
            selections=("question_id", "size"),
            accuracy_when_selected=("correctness_score", "mean"),
        )
        totals = positions.groupby(["model", "prompt_id"])["selections"].transform("sum")
        positions["selection_rate"] = positions["selections"] / totals
    if not positions.empty:
        positions["selected_letter"] = positions["selected_position"].map(
            {1: "A", 2: "B", 3: "C", 4: "D"}
        )
        st.plotly_chart(
            px.bar(
                positions,
                x="selected_letter",
                y="selection_rate",
                color="model",
                barmode="group",
                facet_col="prompt_id",
                hover_data=["selections", "accuracy_when_selected"],
                labels={
                    "selected_letter": "Lettre choisie",
                    "selection_rate": "Part des réponses analysables",
                },
            ),
            width="stretch",
        )

with answers_tab:
    st.subheader("Réponses incorrectes, non analysables ou en erreur")
    issue_rows = issues_mart[
        issues_mart["model"].isin(selected_models)
        & issues_mart["prompt_id"].isin(selected_prompts)
        & issues_mart["category"].isin(selected_categories)
        & issues_mart["difficulty"].isin(selected_difficulties)
        & issues_mart["question_type"].isin(selected_types)
    ].copy()
    st.caption(f"{len(issue_rows):,} observation(s) à examiner après filtres.")
    columns = [
        "model", "prompt_id", "category", "difficulty", "question_type",
        "question", "answer_options", "choices_order", "correct_answer",
        "expected_letter", "ai_answer", "raw_output", "answer_status", "follows_format",
        "response_time", "error",
    ]
    st.dataframe(
        issue_rows[columns].sort_values(
            ["category", "difficulty", "question"], na_position="last"
        ),
        width="stretch",
        hide_index=True,
    )

st.caption("Source : OpenTDB · Les temps sont mesurés côté client et dépendent du matériel local.")
