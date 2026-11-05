# Changelog

Toutes les évolutions notables du projet sont consignées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), versionnage [SemVer](https://semver.org/lang/fr/).
La version de référence est celle de `pyproject.toml`.

## [0.1.0] - 2026-11-05

### Ajouté

- Squelette du paquet `guardbench` (Python 3.11+, `pyproject.toml` comme source de version).
- Objets de base `Sample`, `Verdict`, `Task` et métriques de détection : précision, rappel, F1, FPR, FNR, ROC-AUC, latence p50/p95, intervalles de confiance bootstrap stratifiés.
- Intégration continue GitHub Actions (ruff, pytest, contrôle de version), sans téléchargement de modèle.
