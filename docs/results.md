# Résultats et recommandations

Tous les chiffres de cette page viennent de l'exécution `cpu-baseline` versionnée dans `results/cpu-baseline/`. Les tableaux sont régénérés depuis les fichiers CSV par `python -m guardbench tables`, jamais saisis à la main. Machine de mesure : portable Intel Core i7-1185G7 (4 coeurs, 8 fils), 32 Go de RAM, sans GPU, Windows 11, Python 3.12. La [méthodologie](methodology.md) décrit les données et les métriques.

## Outils exécutés

<!-- table:status:start -->
| Outil | Statut | Détail |
|---|---|---|
| `regex_baseline` | exécuté | 1240 entrées, 0 erreurs, chargement 0 s |
| `presidio` | exécuté | 1240 entrées, 0 erreurs, chargement 18 s |
| `protectai_deberta_v2` | exécuté | 1240 entrées, 0 erreurs, chargement 24 s |
| `gliner2_gliguard` | exécuté | 1240 entrées, 0 erreurs, chargement 121 s |
| `gliner2_pii` | exécuté | 1240 entrées, 0 erreurs, chargement 123 s |
| `llama_guard3_1b` | exécuté | 1240 entrées, 2 erreurs, chargement 0 s |
| `nemo_guardrails` | exécuté | 1240 entrées, 0 erreurs, chargement 6 s |
| `llm_guard` | exécuté | 1240 entrées, 0 erreurs, chargement 44 s |
| `rebuff_heuristic` | exécuté | 130 entrées, 0 erreurs, chargement 0 s |
<!-- table:status:end -->

## Synthèse

<!-- table:overall:start -->
| Outil | J attaques | F1 attaques | J familles revendiquées | FPR bénin FR | p50 (ms) | p95 (ms) | h-machine / 1 000 |
|---|---|---|---|---|---|---|---|
| `gliner2_gliguard` | 0.52 | 0.70 | 0.54 | 0.04 | 370 | 1047 | 0.124 |
| `protectai_deberta_v2` | 0.47 | 0.73 | 0.47 | 0.16 | 471 | 1858 | 0.193 |
| `llm_guard` | 0.30 | 0.72 | 0.38 | 0.26 | 3064 | 14136 | 1.374 |
| `llama_guard3_1b` | 0.30 | 0.63 | 0.37 | 0.01 | 2255 | 7489 | 1.152 |
| `regex_baseline` | 0.27 | 0.53 | 0.24 | 0.03 | 0.3 | 2.7 | 0.000 |
| `nemo_guardrails` | 0.22 | 0.47 | 0.22 | 0.53 | 1405 | 6104 | 0.583 |
| `presidio` | 0.17 | 0.65 | 0.51 | 0.46 | 40 | 179 | 0.016 |
| `gliner2_pii` | 0.14 | 0.65 | 0.77 | 0.14 | 558 | 1845 | 0.209 |
| `rebuff_heuristic` | 0.00 | 0.00 | 0.00 | 0.00 | 111998 | 1035475 | 57.579 |
<!-- table:overall:end -->

## Qualité de détection par famille de risque

<!-- table:youden:start -->
| Outil | Injection directe | Jailbreak | Injection indirecte | Abus d'outils | Toxicité | PII |
|---|---|---|---|---|---|---|
| `gliner2_gliguard` | 0.55 [0.45, 0.65] | 0.75 [0.66, 0.84] | 0.00 [-0.16, 0.14] | 0.78 [0.69, 0.86] | 0.87 [0.80, 0.93] | 0.31 [0.21, 0.41] |
| `protectai_deberta_v2` | 0.56 [0.47, 0.66] | 0.83 [0.76, 0.90] | -0.02 [-0.20, 0.18] | 0.51 [0.39, 0.63] | 0.19 [0.10, 0.29] | 0.37 [0.26, 0.47] |
| `llm_guard` | 0.53 [0.43, 0.64] | 0.42 [0.32, 0.53] | 0.00 [0.00, 0.00] | 0.27 [0.18, 0.36] | 0.27 [0.15, 0.40] | 0.70 [0.60, 0.79] |
| `llama_guard3_1b` | 0.33 [0.23, 0.43] | 0.32 [0.21, 0.42] | -0.12 [-0.22, -0.02] | 0.66 [0.56, 0.76] | 0.42 [0.31, 0.53] | 0.78 [0.70, 0.86] |
| `regex_baseline` | 0.11 [0.05, 0.18] | 0.41 [0.32, 0.51] | 0.00 [-0.20, 0.20] | 0.55 [0.44, 0.66] | 0.13 [0.06, 0.20] | 0.53 [0.43, 0.63] |
| `nemo_guardrails` | 0.32 [0.19, 0.44] | 0.21 [0.08, 0.35] | -0.04 [-0.14, 0.04] | 0.40 [0.31, 0.50] | 0.45 [0.33, 0.57] | -0.10 [-0.20, 0.01] |
| `presidio` | -0.03 [-0.17, 0.11] | 0.32 [0.21, 0.43] | 0.00 [-0.08, 0.08] | 0.38 [0.28, 0.48] | 0.15 [0.03, 0.28] | 0.51 [0.39, 0.61] |
| `gliner2_pii` | 0.14 [0.01, 0.28] | 0.21 [0.10, 0.32] | 0.00 [-0.06, 0.06] | 0.22 [0.13, 0.31] | 0.48 [0.35, 0.59] | 0.77 [0.67, 0.86] |
| `rebuff_heuristic` | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.10 [0.00, 0.30] | 0.00 [0.00, 0.00] |
<!-- table:youden:end -->

<!-- table:rates:start -->
| Outil (rappel / FPR) | Injection directe | Jailbreak | Injection indirecte | Abus d'outils | Toxicité | PII |
|---|---|---|---|---|---|---|
| `gliner2_gliguard` | 0.58 / 0.03 | 0.88 / 0.13 | 0.22 / 0.22 | 0.85 / 0.07 | 0.95 / 0.08 | 0.35 / 0.04 |
| `protectai_deberta_v2` | 0.56 / 0.00 | 0.85 / 0.02 | 0.60 / 0.62 | 0.83 / 0.32 | 0.24 / 0.05 | 0.43 / 0.06 |
| `llm_guard` | 0.62 / 0.09 | 0.95 / 0.53 | 1.00 / 1.00 | 1.00 / 0.73 | 0.48 / 0.21 | 0.81 / 0.11 |
| `llama_guard3_1b` | 0.36 / 0.03 | 0.39 / 0.07 | 0.86 / 0.98 | 0.97 / 0.31 | 0.53 / 0.11 | 0.78 / 0.00 |
| `regex_baseline` | 0.12 / 0.01 | 0.42 / 0.01 | 0.58 / 0.58 | 0.85 / 0.30 | 0.14 / 0.01 | 0.53 / 0.00 |
| `nemo_guardrails` | 0.63 / 0.31 | 0.51 / 0.30 | 0.04 / 0.08 | 0.41 / 0.01 | 0.72 / 0.27 | 0.11 / 0.21 |
| `presidio` | 0.43 / 0.46 | 0.89 / 0.57 | 0.96 / 0.96 | 0.95 / 0.57 | 0.44 / 0.29 | 0.78 / 0.27 |
| `gliner2_pii` | 0.47 / 0.33 | 0.91 / 0.70 | 0.98 / 0.98 | 0.96 / 0.74 | 0.72 / 0.24 | 0.89 / 0.12 |
| `rebuff_heuristic` | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.10 / 0.00 | 0.00 / 0.00 |
<!-- table:rates:end -->

## Seuils et courbes ROC

<!-- table:auc:start -->
| Outil (ROC-AUC) | Injection directe | Jailbreak | Injection indirecte | Abus d'outils | Toxicité | PII |
|---|---|---|---|---|---|---|
| `gliner2_gliguard` | 0.86 | 0.92 | 0.54 | 0.96 | 0.97 | 0.81 |
| `protectai_deberta_v2` | 0.91 | 0.97 | 0.45 | 0.85 | 0.57 | 0.91 |
| `llm_guard` | 0.77 | 0.79 | 0.50 | 0.68 | 0.64 | 0.86 |
| `llama_guard3_1b` | 0.85 | 0.85 | 0.50 | 0.95 | 0.79 | 0.98 |
| `presidio` | 0.48 | 0.66 | 0.50 | 0.77 | 0.57 | 0.82 |
| `gliner2_pii` | 0.58 | 0.64 | 0.49 | 0.72 | 0.77 | 0.94 |
| `rebuff_heuristic` | 0.49 | 0.85 | 0.51 | 0.80 | 0.70 | 0.39 |
<!-- table:auc:end -->

## Sur-blocage en français

<!-- table:french:start -->
| Outil | FPR instructions French-Alpaca (n = 100) | FPR pièges lexicaux (n = 40) |
|---|---|---|
| `gliner2_gliguard` | 0.03 | 0.07 |
| `protectai_deberta_v2` | 0.07 | 0.40 |
| `llm_guard` | 0.21 | 0.40 |
| `llama_guard3_1b` | 0.00 | 0.03 |
| `regex_baseline` | 0.02 | 0.05 |
| `nemo_guardrails` | 0.44 | 0.75 |
| `presidio` | 0.52 | 0.33 |
| `gliner2_pii` | 0.13 | 0.15 |
| `rebuff_heuristic` | 0.00 | 0.00 |
<!-- table:french:end -->

## Couverture des risques

<!-- table:coverage:start -->
| Outil | Injection directe | Jailbreak | Injection indirecte | Abus d'outils | Toxicité | PII |
|---|---|---|---|---|---|---|
| `gliner2_gliguard` | revendiqué, mesuré | revendiqué, mesuré | revendiqué, non atteint | mesuré seul | revendiqué, mesuré |  |
| `protectai_deberta_v2` | revendiqué, mesuré | revendiqué, mesuré | revendiqué, non atteint | revendiqué, non atteint |  |  |
| `llm_guard` | revendiqué, mesuré | revendiqué, non atteint | revendiqué, non atteint |  | revendiqué, non atteint | revendiqué, mesuré |
| `llama_guard3_1b` |  | revendiqué, non atteint |  |  | revendiqué, mesuré | mesuré seul |
| `regex_baseline` | revendiqué, non atteint | revendiqué, non atteint | revendiqué, non atteint |  | revendiqué, non atteint | revendiqué, mesuré |
| `nemo_guardrails` | revendiqué, non atteint | revendiqué, non atteint |  |  | revendiqué, non atteint | revendiqué, non atteint |
| `presidio` |  |  |  |  |  | revendiqué, non atteint |
| `gliner2_pii` |  |  |  |  |  | revendiqué, mesuré |
| `rebuff_heuristic` | revendiqué, non atteint |  | revendiqué, non atteint |  |  |  |
<!-- table:coverage:end -->

## Latence et coût

Les latences sont mesurées une entrée à la fois, sur CPU, après chauffe. Trois ordres de grandeur se dégagent.

- **Moins d'une milliseconde à quelques dizaines** : la référence par motifs (0,3 ms en médiane) et Presidio (40 ms). Ils tiennent dans n'importe quel chemin de requête.
- **Quelques centaines de millisecondes** : les encodeurs, GLiNER2 en mode garde-fou (370 ms) et DeBERTa de Protect AI (471 ms). Acceptables devant un modèle qui met lui-même plusieurs secondes à répondre, et dix fois moins chers avec un GPU.
- **Plusieurs secondes** : les juges LLM locaux, Llama Guard 3 1B (2,3 s) et NeMo avec Qwen2.5 1.5B (1,4 s), ainsi que LLM Guard (3,1 s en médiane, 14 s au p95), qui enchaîne plusieurs scanners.

Rebuff sort du cadre. Son module heuristique compare chaque entrée à toutes les phrases d'attaque qu'il génère, un coût quadratique en longueur de texte : 112 s en médiane par entrée et 57,6 heures-machine pour 1 000 entrées. C'est pour cela qu'il n'a tourné que sur un échantillon de 10 entrées par classe (130 au total). Ses aires sous la courbe reposent sur une dizaine d'exemples par famille et ne se comparent pas aux autres.

## Recommandations par contexte

| Contexte | Choix | Pourquoi |
|---|---|---|
| Entrée d'un assistant grand public, en anglais et en français | GLiNER2 en mode garde-fou | meilleur J sur les attaques (0,52), peu de sur-blocage en français (3 % sur des consignes ordinaires, 7 % sur les pièges lexicaux), 370 ms |
| Assistant en anglais, injection directe et jailbreak avant tout | DeBERTa de Protect AI | meilleures AUC sur ces deux familles (0,91 et 0,97), mais 40 % de faux positifs sur les pièges lexicaux français, à recalibrer avant tout usage en français |
| Agent qui appelle des outils | GLiNER2 ou Llama Guard 3 1B | AUC de 0,96 et 0,95 sur l'abus d'outils. Llama Guard ne sur-bloque presque pas le français (0 % et 3 %) mais coûte 2,3 s par appel |
| Fuite de données personnelles | GLiNER2 en mode PII, ou Llama Guard 3 1B | J de 0,77 sur sa famille revendiquée pour le premier, AUC de 0,98 pour le second. Presidio est rapide mais bloque 52 % des consignes françaises ordinaires |
| Toxicité en sortie | GLiNER2 en mode garde-fou | AUC de 0,97 |
| Préfiltre gratuit | référence par motifs | 0,3 ms et peu de faux positifs, à placer devant un vrai classifieur, jamais seule (rappel de 49 % sur les attaques) |

Deux constats valent quel que soit le contexte.

- **L'injection indirecte n'est arrêtée par aucun outil.** Toutes les AUC tournent autour de 0,5, c'est-à-dire le hasard. Une consigne cachée dans une page ou un document récupéré se lit comme du texte ordinaire. La parade est architecturale : séparer les données des instructions, réduire les droits des outils, demander une confirmation humaine avant une action irréversible.
- **Un juge LLM trop petit sur-bloque.** NeMo avec Qwen2.5 1.5B refuse 44 % des consignes françaises ordinaires et 75 % des pièges lexicaux. Ce n'est pas un défaut de NeMo lui-même mais du modèle qu'on lui confie. Un juge de cette taille ne convient pas à la production.

Rebuff, dans sa version heuristique, n'est pas utilisable : au seuil par défaut de son SDK (0,75), il n'a signalé qu'une entrée sur 130, son score ne dépassant jamais 0,77. Lakera Guard et Prompt-Guard n'ont pas pu être mesurés, faute de clé et de licence acceptée.

## F1 par famille, pour comparaison avec la littérature

<!-- table:f1:start -->
| Outil | Injection directe | Jailbreak | Injection indirecte | Abus d'outils | Toxicité | PII |
|---|---|---|---|---|---|---|
| `gliner2_gliguard` | 0.72 [0.64, 0.79] | 0.88 [0.83, 0.92] | 0.31 [0.17, 0.44] | 0.89 [0.84, 0.93] | 0.94 [0.90, 0.97] | 0.50 [0.40, 0.60] |
| `protectai_deberta_v2` | 0.72 [0.64, 0.80] | 0.91 [0.87, 0.95] | 0.54 [0.45, 0.64] | 0.77 [0.71, 0.82] | 0.37 [0.26, 0.47] | 0.58 [0.48, 0.66] |
| `llm_guard` | 0.73 [0.65, 0.80] | 0.77 [0.73, 0.81] | 0.67 [0.67, 0.67] | 0.73 [0.71, 0.76] | 0.57 [0.48, 0.66] | 0.84 [0.79, 0.89] |
| `llama_guard3_1b` | 0.52 [0.41, 0.61] | 0.53 [0.43, 0.63] | 0.61 [0.56, 0.65] | 0.85 [0.82, 0.89] | 0.65 [0.56, 0.73] | 0.88 [0.82, 0.92] |
| `regex_baseline` | 0.21 [0.11, 0.32] | 0.59 [0.49, 0.68] | 0.54 [0.43, 0.64] | 0.79 [0.74, 0.84] | 0.24 [0.15, 0.34] | 0.69 [0.60, 0.77] |
| `nemo_guardrails` | 0.65 [0.58, 0.72] | 0.56 [0.48, 0.65] | 0.07 [0.00, 0.17] | 0.58 [0.48, 0.67] | 0.72 [0.66, 0.79] | 0.17 [0.08, 0.25] |
| `presidio` | 0.46 [0.37, 0.54] | 0.72 [0.68, 0.76] | 0.66 [0.63, 0.68] | 0.75 [0.72, 0.79] | 0.51 [0.42, 0.59] | 0.76 [0.70, 0.81] |
| `gliner2_pii` | 0.52 [0.44, 0.60] | 0.70 [0.66, 0.74] | 0.66 [0.64, 0.68] | 0.71 [0.68, 0.74] | 0.73 [0.66, 0.79] | 0.89 [0.84, 0.93] |
| `rebuff_heuristic` | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.18 [0.00, 0.46] | 0.00 [0.00, 0.00] |
<!-- table:f1:end -->
