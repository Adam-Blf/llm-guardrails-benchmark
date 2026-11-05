# Changelog

Toutes les évolutions notables du projet sont consignées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versionnage [SemVer](https://semver.org/lang/fr/).
La version de référence est celle de `pyproject.toml`.

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
