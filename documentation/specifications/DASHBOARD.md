# Spécification proposée — Dashboard de benchmark

**Statut : implémentée.** Cette spécification s’appuie sur les marts dbt et l’observation Silver question × modèle × prompt. L’application est dans `app.py`.

## Objectif utilisateur

Comparer les modèles et prompts évalués, repérer les thèmes ou niveaux où ils réussissent moins bien, et examiner les réponses incorrectes ou non analysables.

## Utilisateurs et usage

Le dashboard est destiné à l’équipe projet et au correcteur. Il sert à explorer les résultats du benchmark après exécution; il ne lance pas d’appels aux modèles.

## Filtres

- Modèle et version de prompt.
- Catégorie, difficulté et type de question.
- Valeurs par défaut : toutes les valeurs disponibles.
- Les filtres s’appliquent à tous les onglets et tableaux.

## Indicateurs clés

- **Précision** : part des réponses analysables correspondant à la bonne lettre; afficher aussi le nombre de réponses notées.
- **Baseline aléatoire** : moyenne de `random_baseline` sur les observations filtrées, pour comparer les résultats à la probabilité de réussite au hasard.
- **Écart à la baseline** : `accuracy - random_baseline`, pour quantifier le gain par rapport au hasard.
- **Respect du format** et **taux non analysable** : indiquent si le modèle suit la consigne de réponse par lettre.
- **Latence** : médiane et p95 en secondes; l’average peut être présenté dans le détail.
- **Erreurs d’appel** : nombre d’erreurs runtime conservées.

## Onglets proposés

### Vue générale

Classement modèle × prompt avec précision, baseline aléatoire, nombre de réponses notées, respect du format et latences médiane/p95. La précision et la baseline sont affichées ensemble pour le même périmètre filtré.

### Catégories et difficulté

- Précision et baseline par catégorie.
- Précision par difficulté et type de question (QCM ou vrai/faux), car le hasard n’a pas la même probabilité selon le nombre de choix.
- Afficher le nombre d’observations pour contextualiser les taux.

### Temps et robustesse

- Distribution de `response_time` par modèle.
- Taux de respect du format, réponses non analysables et erreurs d’appel.
- Fréquence de chaque lettre/position choisie et précision à chaque position, pour repérer un biais de position.
- Distinguer une réponse incorrecte d’une réponse non analysable et d’une erreur runtime.

### Réponses à examiner

Table filtrable des réponses incorrectes, non analysables ou en erreur. Afficher la question, la catégorie, la difficulté, le type, les choix dans leur ordre présenté, la réponse correcte, la sortie brute et la lettre analysée.

## Sources de données

- Base locale : `gold/benchmark.duckdb`.
- Agrégats : `marts.mart_model_prompt`, `marts.mart_category_performance`, `marts.mart_difficulty_performance`.
- Marts exploratoires : `marts.mart_position_bias`, `marts.mart_answer_issues`.
- Détails de réponse : `staging.stg_benchmark` ou `silver/obt_answers.parquet`.
- Pour le classement, exposer aussi `random_baseline` dans `mart_model_prompt` afin que le dashboard consomme un agrégat métier complet.

## États et comportements

- Si la base ou les tables sont absentes, expliquer comment lancer la transformation dbt.
- Si aucun résultat ne correspond aux filtres, afficher un état vide clair.
- Montrer le nombre d’observations après filtres et le périmètre utilisé pour chaque métrique.
- Les sorties brutes ne sont visibles que dans l’onglet des réponses à examiner.

## Critères d’acceptation

- Les filtres modèle/prompt et les filtres thématiques changent tous les graphiques et tableaux concernés.
- Le classement permet de comparer précision et baseline aléatoire pour les mêmes filtres.
- Les graphiques catégorie et difficulté indiquent leurs volumes d’observations.
- Une réponse non analysable n’est pas comptée comme correcte ou incorrecte dans le taux de précision, et reste visible dans l’explorateur.
- Le dashboard distingue latence, erreur runtime, non-respect du format et erreur de connaissance.
- L’interface reste utilisable sans données et avec les résultats partiels d’un run.
