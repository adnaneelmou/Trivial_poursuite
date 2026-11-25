# Consignes de travail — Jouons au Trivial Poursuite

## Contexte

Projet pédagogique de data engineering : construire un benchmark de culture générale à partir des questions d’Open Trivia Database (OpenTDB), puis analyser les réponses d’un modèle d’IA local.

## Objectifs du projet

- Constituer un jeu de questions de culture générale et conserver les réponses de référence.
- Évaluer un ou plusieurs modèles locaux, mesurer leurs réponses et leur temps de génération.
- Préparer des données adaptées à l’analyse des performances globales, par thème, difficulté, modèle et prompt.
- Produire un rapport interactif et préparer une présentation orale d’environ 10 minutes avec questions/réponses.
- Livrer un dépôt compréhensible et reproductible, accompagné d’un README de setup et d’utilisation.

## Contraintes connues du sujet

- Le projet doit suivre une architecture en médaillon avec des couches Bronze, Silver et Gold.
- Les données de questions proviennent de l’API publique OpenTDB. Respecter ses limites d’utilisation et attribuer la source selon sa licence.
- Les réponses brutes des modèles doivent être conservées dans le flux de données afin que le résultat du benchmark reste traçable.
- Le projet doit intégrer un runtime local de modèles d’IA, dbt, DuckDB et une application Streamlit.
- Les résultats doivent garder la trace du modèle, du prompt et du temps de réponse.

## Règles permanentes

- Adresse-toi à l’utilisateur en l’appelant « Ad ».
- Traite une conversation comme une micro-tâche précise. Si une nouvelle tâche est nécessaire, explique brièvement le lien avec le travail en cours.
- Guide l’utilisateur étape par étape et explique les choix afin qu’il puisse les défendre à l’oral.
- Ne prends pas de décision métier ou d’architecture structurante sans en discuter avec l’utilisateur. Présente les options et leurs conséquences avant d’arbitrer.
- Pour une nouvelle fonctionnalité, commence par comprendre le besoin et les contraintes; ne commence pas l’implémentation avant que le périmètre soit clair.
- Garde la documentation courte, utile et sans répétitions. Mets à jour `documentation/CURRENT.md` à la fin de chaque tâche significative, une fois ce fichier créé.
- N’effectue pas de commit ni de push GitHub sans demande explicite de l’utilisateur. Quand ils sont demandés, privilégie des commits petits et descriptifs.
- Utilise le français pour les échanges et la documentation du projet, sauf demande contraire.

## Documentation du projet

- `README.md` : comprendre, installer et utiliser le projet; destiné aux humains.
- `documentation/ARCHITECTURE.md` : décisions d’architecture retenues et leurs raisons.
- `documentation/CURRENT.md` : état d’avancement, tâche en cours, blocages et prochaine étape.
- `documentation/DECISIONS.md` : décisions métier et fonctionnelles avec leur justification.
- `documentation/specifications/` : spécifications détaillées par fonctionnalité, seulement lorsqu’elles sont utiles.

Lire les documents pertinents avant de modifier une partie du projet. Éviter de recopier leur contenu dans ce fichier; `AGENTS.md` donne les règles de collaboration générales.
