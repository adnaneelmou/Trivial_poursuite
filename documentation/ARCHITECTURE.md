# Architecture du projet

## Flux de données

```text
OpenTDB ───────────────┐
                       ├─> Bronze ─> transformation Python ─> Silver Parquet
LM Studio / modèle ────┘                                      │
                                                              v
                                                dbt : staging → intermediate → marts
                                                              │
                                                              v
                                              Gold : base DuckDB → dashboard Streamlit
```

Le dashboard est implémenté dans `app.py`. Cette page décrit l’organisation actuellement en place.

## Couches et granularité

- **Bronze** — `bronze/questions_raw.csv` conserve les questions OpenTDB et leur réponse de référence. `bronze/ai_answers_raw.csv` conserve une observation par question, modèle et prompt, avec la sortie brute, la lettre analysée, la justesse, le temps, le texte du prompt, l’ordre des choix et les erreurs éventuelles.
- **Silver** — `silver/obt_answers.parquet` joint les réponses du modèle aux questions. Une ligne représente une observation question × modèle × prompt. `silver/questions.parquet` est le Parquet propre des questions, conservé comme étape intermédiaire de préparation.
- **Gold** — `gold/benchmark.duckdb` contient les relations construites par dbt : `staging.stg_benchmark` (vue), `intermediate.int_question_results` (table avec statut, score, baseline et positions), puis les marts de performance par modèle/prompt, catégorie, difficulté/type, biais de position et erreurs.

## Code et configuration

- `src/collect.py` collecte les questions OpenTDB et `src/complete_bronze.py` réconcilie les comptes par catégorie.
- `src/prompts.py` contient les formulations versionnées. `src/run_benchmark.py` interroge le serveur local LM Studio, accepte le choix du prompt et ajoute les réponses dans Bronze. Le traitement est reprenable à partir des clés question × modèle × prompt.
- `src/prepare_silver.py` prépare le Parquet de questions; `src/bronze_to_silver.py` joint les réponses aux questions.
- `dbt_project.yml` définit `src/models` comme répertoire dbt et `src/macros` comme répertoire des macros. `profiles.yml` pointe vers DuckDB local.
- `requirements.txt` épingle les dépendances Python. `.venv` est l’environnement local, créé avec Python 3.12.

## Scoring et indicateurs

Le modèle reçoit des choix étiquetés par lettres, mélangés de façon reproductible pour chaque `question_id`. Le scoring reconnaît une lettre ou le texte exact d’un choix et le compare à la réponse attendue. `follows_format` indique si la sortie est uniquement une lettre. Les sorties brutes, les sorties non analysables et les erreurs restent conservées pour permettre l’audit. Les marts calculent la précision, le respect du format, les erreurs, la baseline aléatoire selon le nombre de choix et les latences.

## Source et couverture

OpenTDB est interrogé via son API publique avec un jeton de session et une cadence respectant sa limite de requêtes. Le snapshot Bronze contient actuellement 5 299 questions vérifiées; ce compte peut évoluer avec la source. Les données OpenTDB sont sous licence [CC BY-SA 4.0](https://opentdb.com/api_config.php).
