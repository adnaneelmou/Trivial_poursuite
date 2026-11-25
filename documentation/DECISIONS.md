# Décisions du projet

Les décisions ci-dessous décrivent les choix actuellement mis en œuvre. Elles peuvent évoluer si le benchmark ou les besoins de présentation le justifient.

| Sujet | Décision actuelle | Justification / conséquence |
|---|---|---|
| Source de questions | OpenTDB via API publique, collecte par jeton et par pages | Source catégorisée adaptée à la culture générale; les limites d’API et la couverture du snapshot doivent être suivies. |
| Identifiant de question | SHA-256 du contenu canonique complet de la question, y compris les choix | Évite de fusionner deux enregistrements ayant le même énoncé et la même réponse correcte, mais des choix différents. |
| Bronze | CSV séparés pour questions brutes et réponses IA brutes | Conserve l’entrée source et la sortie modèle sans les mélanger avant transformation. |
| Comparaison des prompts | Deux formulations sont disponibles : une consigne stricte demandant une lettre seule (`v1_letter_only`) et une question simple (`v2_simple`) | Même question et mêmes choix; les sorties peuvent être scorées par lettre ou par correspondance exacte avec un choix. `follows_format` mesure les réponses composées d’une lettre seule. |
| Ordre des choix | Mélange initialisé par `question_id` | Un même ordre est réutilisé d’un run à l’autre et entre modèles. |
| Modèle de référence | `google/gemma-4-e4b` servi localement par LM Studio | Runtime local choisi pour le benchmark initial; le protocole permet d’ajouter d’autres modèles. |
| Paramètres de génération | Température 0, sortie courte, `reasoning_effort=none` | Réduit la variabilité et demande une réponse compacte, adaptée au format lettre. |
| Reprise des runs | Une observation terminée est identifiée par question × modèle × prompt | Permet de reprendre un benchmark interrompu sans refaire les lignes déjà écrites. |
| Silver | Parquet en table jointe question × modèle × prompt | Format typé et exploitable pour les transformations analytiques; permet plusieurs observations par question. |
| Transformations analytiques | dbt avec adaptateur DuckDB; vues staging, table intermediate et marts Gold | Rend le lignage des indicateurs visible et produit des tables orientées questions métier. |
| Classification des observations | Intermediate classe chaque ligne comme correcte, incorrecte, non analysable ou erreur runtime | Sépare la connaissance du modèle des problèmes de format et d’appel. |
| Biais de position | Gold agrège les positions choisies par modèle et prompt | Vérifie si le modèle préfère une position de réponse après le mélange reproductible des choix. |
| Environnement local | Python 3.12 dans `.venv` | Compatible avec l’installation dbt retenue; les dépendances directes sont épinglées. |

## À arbitrer plus tard

- L’étendue de la comparaison du prompt simple (pilote ou benchmark complet, et modèles concernés).
- Les autres modèles à comparer sur l’ensemble des questions.
- Les filtres, vues et interactions définitifs du dashboard Streamlit.
- La façon de publier ou partager les données générées et la base DuckDB.
