# État actuel du projet

## Terminé

- Création des dossiers de travail Bronze, Silver, Gold, `src/` et dbt.
- Installation de Python 3.12 dans `.venv`, avec les dépendances projet épinglées dans `requirements.txt`.
- Collecte et contrôle de couverture OpenTDB : 5 299 questions vérifiées, avec réponses de référence et choix.
- Ajout de `src/collect.py` et `src/complete_bronze.py` pour la collecte et la réconciliation des questions.
- Préparation de `silver/questions.parquet` à partir des questions Bronze.
- Installation et configuration de LM Studio avec le modèle `google/gemma-4-e4b`; vérification d’un appel local.
- Création de `src/run_benchmark.py` : choix mélangés de façon déterministe, réponse attendue sous forme de lettre, reprise des observations déjà enregistrées et stockage des réponses brutes dans `bronze/ai_answers_raw.csv`.
- Pilote de 10 questions : 8 réponses correctes, 10 sorties au bon format, aucune erreur d’appel. La latence médiane observée était d’environ 0,52 seconde, avec deux premiers appels beaucoup plus lents.
- Création de `src/bronze_to_silver.py` et des modèles/configurations dbt pour préparer les couches d’analyse.
- Création de `src/bronze_to_silver.py` puis production de `silver/obt_answers.parquet` avec 5 299 observations jointes.
- Construction dbt réussie dans `gold/benchmark.duckdb` : staging, intermediate et trois marts de performance.
- Ajout de `.gitignore` pour l’environnement virtuel, les sorties dbt et les fichiers DuckDB locaux.
- Création de `AGENTS.md` avec le contexte du projet et les règles permanentes de collaboration.
- Documentation de l’architecture et des décisions actuelles dans `documentation/ARCHITECTURE.md` et `documentation/DECISIONS.md`.
- Rédaction de la proposition de dashboard dans `documentation/specifications/DASHBOARD.md`.
- Implémentation de `app.py` : filtres globaux, KPIs, classement modèle/prompt, analyses par catégorie/difficulté, latence et explorateur des réponses à examiner.
- Ajout de la baseline aléatoire au mart modèle/prompt et reconstruction dbt réussie.
- Enrichissement d’intermediate avec le statut de réponse et les positions choisie/attendue; ajout des marts d’écart à la baseline, biais de position et erreurs.
- Extension du dashboard avec une visualisation du biais de position et l’utilisation du mart d’erreurs.
- Benchmark complet de `qwen/qwen3.5-9b` : 5 299 réponses enregistrées dans Bronze, puis intégrées dans Silver.
- Reconstruction dbt réussie après intégration de Qwen : 7 modèles exécutés dans DuckDB, sans erreur.
- Création de `src/prompts.py` avec le prompt strict existant (`v1_letter_only`) et une variante simple (`v2_simple`); ajout de l’option `--prompt` au script de benchmark.
- Adaptation du scoring pour reconnaître une lettre ou le texte exact d’un choix; les deux prompts utilisent le même budget de sortie de 32 tokens.
- Pilote Qwen de 10 questions avec `v2_simple` terminé : 7 bonnes réponses, 8 réponses analysables, 2 sorties tronquées avant le choix, aucun échec d’appel; aucune réponse n’était au format lettre seule.
- Correction du parseur pour reconnaître les formulations explicites comme « La bonne réponse est B »; champs dérivés recalculés pour les 10 lignes, sans modifier les sorties brutes.

## En attente

- Ajuster le prompt simple ou son budget de sortie, puis refaire un pilote court avec un nouvel identifiant de prompt; ne pas lancer le run complet tant que les réponses sont correctement évaluables.
- Finaliser l’analyse et le README avant la dernière étape de validation du dashboard.

## Prochaine étape

Le pilote de `v2_simple` montre que le modèle produit des explications qui dépassent parfois le budget de 32 tokens. Ajuster cette variante ou le budget, en gardant un nouvel identifiant pour ne pas mélanger des formulations différentes. Refaire un pilote, puis comparer les prompts sur les mêmes questions et le même modèle. Ensuite, finaliser l’analyse, le README et la préparation de l’oral. La validation finale du dashboard sera la dernière étape. Les tests dbt et les tests automatisés ne sont pas encore exécutés.

## Résultat du benchmark

- Benchmark complet terminé pour `google/gemma-4-e4b` avec `v1_letter_only` : 5 299 observations.
- Benchmark complet terminé pour `qwen/qwen3.5-9b` avec `v1_letter_only` : 5 299 observations, 3 768 bonnes réponses (71,1 %), aucune erreur d’appel; temps moyen d’environ 1,44 s.
- Sur le même prompt et les mêmes questions, `google/gemma-4-e4b` a obtenu 3 340 bonnes réponses (63,0 %), sans erreur d’appel; temps moyen d’environ 0,51 s.
- Comparaison avec `google/gemma-4-12b` commencée puis arrêtée à la demande : 66 observations sauvegardées. Le run peut reprendre avec `--all`, qui sautera ces lignes.
- Pilote Bonsai 27B (`prism-ml/bonsai-27b`) : 10 observations, 7 correctes, 10 sorties au format lettre, aucune erreur runtime; latence médiane 3,04 s. Benchmark complet non lancé.
- Les benchmarks enregistrent 10 674 observations au total sur quatre modèles; un résultat pour Gemma 4 E4B et deux pour Gemma 4 12B sont non analysables comme lettre et conservés pour l’analyse.
- `silver/obt_answers.parquet` contient 10 674 observations sur 5 299 identifiants de question; quatre modèles et un prompt.
- Bronze contient aussi un pilote additionnel de 10 questions Qwen sous `v2_simple`; Silver et Gold ne l’intègrent pas encore.
