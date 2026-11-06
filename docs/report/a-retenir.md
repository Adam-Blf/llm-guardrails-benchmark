# À retenir

- Aucun guardrail ne couvre toutes les familles de risque : le choix dépend du risque visé, de la langue des utilisateurs et du budget de latence.
- GLiNER2 en mode garde-fou offre le meilleur équilibre pour filtrer l'entrée d'un assistant bilingue (J de 0,52, 3 % de faux positifs sur le français ordinaire, 370 ms).
- DeBERTa de Protect AI est le plus fort sur l'injection directe et le jailbreak en anglais, mais refuse 40 % des pièges lexicaux français.
- L'injection indirecte n'est détectée par aucun outil mesuré : elle se traite par l'architecture (séparation données et consignes, droits réduits, validation humaine).
- Un juge LLM trop petit sur-bloque : NeMo avec Qwen2.5 1.5B refuse 44 % des consignes françaises ordinaires.
- Rebuff heuristique ne se déclenche presque jamais à son seuil par défaut et coûte près de deux minutes par entrée.
- Avec cent exemples par classe, les intervalles de confiance (bootstrap à 95 %) couvrent plusieurs points : deux outils dont les J diffèrent de moins de 0,05 ne se départagent pas.
- Tout se rejoue en une commande (`python -m guardbench run`), sur CPU, sur Colab ou avec Docker.
