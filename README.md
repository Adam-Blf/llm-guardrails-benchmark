# llm-guardrails-benchmark

<!-- adam-badges:start -->
[![version](https://img.shields.io/badge/version-0.6.0-163767?style=flat-square)](CHANGELOG.md)
[![CI](https://img.shields.io/github/actions/workflow/status/Adam-Blf/llm-guardrails-benchmark/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Adam-Blf/llm-guardrails-benchmark/actions/workflows/ci.yml)
[![commits](https://img.shields.io/github/commit-activity/t/Adam-Blf/llm-guardrails-benchmark?color=001329&label=commits&style=flat-square)](https://github.com/Adam-Blf/llm-guardrails-benchmark/commits)
[![visites](https://hits.sh/github.com/Adam-Blf/llm-guardrails-benchmark.svg?style=flat-square&label=visites&color=001329)](https://hits.sh/github.com/Adam-Blf/llm-guardrails-benchmark/)
[![last commit](https://img.shields.io/github/last-commit/Adam-Blf/llm-guardrails-benchmark?color=D4A437&style=flat-square&label=dernier%20push)](https://github.com/Adam-Blf/llm-guardrails-benchmark/commits)
[![top language](https://img.shields.io/github/languages/top/Adam-Blf/llm-guardrails-benchmark?style=flat-square)](https://github.com/Adam-Blf/llm-guardrails-benchmark)
[![license](https://img.shields.io/github/license/Adam-Blf/llm-guardrails-benchmark?style=flat-square&color=D4A437)](LICENSE)
<!-- adam-badges:end -->

Benchmark de guardrails pour la sécurité des LLM et des agents LLM. Projet du cours MLOps (XDE826) du Mastère Data Engineering et IA de l'EFREI.

Le dépôt est en construction. Le paquet `guardbench` porte les jeux de données, les adaptateurs d'outils, le runner et l'analyse. Les résultats et le rapport arrivent dans les versions suivantes.

## Lancer avec Docker

Une seule commande construit l'image, démarre Ollama, télécharge Llama Guard 3 1B et Qwen2.5 1.5B, puis exécute tous les outils CPU, l'analyse et les figures :

```bash
docker compose up --build
```

Les résultats arrivent dans `results/docker-cpu` (variable `RUN_NAME` pour changer de nom). Les clés facultatives (`LAKERA_API_KEY`, `HF_TOKEN`) se placent dans un fichier `.env` copié depuis `.env.example`.

## Lancer sur Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Adam-Blf/llm-guardrails-benchmark/blob/main/notebooks/benchmark_colab.ipynb)

Le notebook `notebooks/benchmark_colab.ipynb` relance le même CLI sur un GPU T4 gratuit, avec 250 exemples par classe et des modèles plus lourds (Llama Guard 3 1B et 8B via `transformers`, Prompt-Guard-86M). Il écrit dans `results/colab-gpu` puis propose les résultats en archive zip. Les latences GPU sont rapportées à part et ne se comparent pas aux latences CPU.

## Auteurs

- Adam Beloucif ([Adam-Blf](https://github.com/Adam-Blf))
- Emilien Morice ([emilien754](https://github.com/emilien754))
