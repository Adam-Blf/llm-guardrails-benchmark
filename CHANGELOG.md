# Changelog

Toutes les évolutions notables du projet sont consignées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versionnage [SemVer](https://semver.org/lang/fr/).
La version de référence est celle de `pyproject.toml`.

## [1.0.0] - 2026-11-06

### Ajouté

- Exécution de référence `cpu-baseline` complète : neuf outils sur 1 240 entrées, LLM Guard compris. Rebuff a tourné sur un échantillon de 10 entrées par classe (`max_per_class`), son heuristique coûtant près de deux minutes par entrée.
- Tableaux régénérés depuis les CSV (`python -m guardbench tables`) dans `docs/results.md` et le README, sections « Latence et coût » et « Recommandations par contexte » rédigées.
- Rapport PDF complet (14 pages) : résumé et synthèse des outils sur la couverture, encadré « À retenir » sous le sommaire, conclusion.
- `scripts/check_report.py` refuse le texte de remplissage (« texte de test », « lorem ipsum », « TODO ») et contrôle aussi la couverture et le sommaire.

### Corrigé

- `guardbench tables` n'insérait rien dans un bloc vide ni dans un fichier en CRLF, tout en annonçant un succès. Test de non-régression sur les deux cas.
- La couverture du rapport affichait la version figée à l'installation du paquet, et non celle de `pyproject.toml`.

## [0.6.0] - 2026-11-05

### Ajouté

- J de Youden (rappel moins FPR) par tranche, avec son intervalle bootstrap, et moyenne par outil. Il remplace le F1 comme indicateur de classement : un outil qui bloque tout obtient F1 = 0,67 sur une tranche équilibrée mais J = 0.
- Figures matplotlib : cartes de chaleur J et F1, F1 avec IC 95 %, rappel contre FPR, courbes ROC, latence p50 et p95, sur-blocage en français.
- `docs/methodology.md` : choix des outils, des données, des métriques, protocole de latence et menaces à la validité.

## [0.5.0] - 2026-11-05

### Ajouté

- `Dockerfile` et `docker-compose.yml` : benchmark CPU complet en une commande, Ollama et ses modèles compris, versions figées par `docker/constraints.txt`.
- Notebook Colab `notebooks/benchmark_colab.ipynb` pour une exécution GPU plus large, rangée dans `results/colab-gpu`.
- Llama Guard 3 8B chargé en 4 bits sur GPU pour tenir dans les 16 Go d'un T4.
- Workflow de release sur tag : contrôle de version, wheel et sdist, notes tirées du CHANGELOG, image publiée sur GHCR.

## [0.4.0] - 2026-11-05

### Ajouté

- Runner : chaque outil passe sur toute la suite, trois appels de chauffe exclus de la latence, écriture au fil de l'eau et reprise sans doublon d'une exécution interrompue.
- Exécution multi-processus pour les outils purement Python (Rebuff), la latence restant mesurée appel par appel dans chaque processus.
- Analyse : tables par outil et famille de risque, par source, synthèse par outil et matrice de couverture revendiquée ou mesurée.
- Interface en ligne de commande `python -m guardbench` (`run`, `analyse`, `figures`, `report`, `list`).

## [0.3.0] - 2026-11-05

### Ajouté

- Interface commune `Guardrail` (décision, score, latence, erreurs isolées) et registre d'adaptateurs à import paresseux.
- Adaptateurs : référence regex EN et FR, Rebuff (couche heuristique), DeBERTa v2 de Protect AI, Prompt-Guard-86M, GLiNER2 GLiGuard et GLiNER2 PII, Presidio (EN et FR), LLM Guard, Llama Guard 3 via Ollama ou transformers, NeMo Guardrails (rail `self check input` sur Ollama), Lakera Guard.
- Les outils inaccessibles (clé API absente, modèle à licence, service arrêté) sont sautés avec une raison écrite, jamais en plein milieu d'une exécution.

## [0.2.0] - 2026-11-05

### Ajouté

- Sept tranches de données étiquetées, une par famille de risque : injection directe (deepset, safe-guard), jailbreak (jackhhao), injection indirecte (courriels BIPIA, appariés propre ou piégé), abus d'outils d'agent (réponses d'outils InjecAgent), toxicité (ToxicChat), fuite de PII (ai4privacy EN et FR) et un jeu bénin français avec 40 faux positifs difficiles écrits à la main.
- Sources épinglées par révision (commit Hub ou Git), cache local, échantillonnage stratifié à graine fixe.

### Modifié

- Champ `license` du `pyproject.toml` au format SPDX.

## [0.1.0] - 2026-11-05

### Ajouté

- Squelette du paquet `guardbench` (Python 3.11+, `pyproject.toml` comme source de version).
- Objets de base `Sample`, `Verdict`, `Task` et métriques de détection : précision, rappel, F1, FPR, FNR, ROC-AUC, latence p50/p95, intervalles de confiance bootstrap stratifiés.
- Intégration continue GitHub Actions (ruff, pytest, contrôle de version), sans téléchargement de modèle.
