# Conclusion

Un guardrail n'est pas une protection globale, c'est un détecteur spécialisé, et la question utile n'est pas « quel est le meilleur outil » mais « contre quel risque, dans quelle langue, à quel coût ». Sur notre suite, les encodeurs récents, GLiNER2 en tête, offrent le meilleur rapport entre détection, sur-blocage et latence pour filtrer l'entrée d'un assistant. Les juges LLM couvrent plus large mais coûtent plusieurs secondes, et un juge trop petit sur-bloque au point de devenir inutilisable. Les outils historiques à base d'heuristiques, Rebuff en tête, ne tiennent plus face aux attaques actuelles.

Le résultat le plus net est négatif : aucun outil ne détecte l'injection indirecte. Une application qui donne à un agent l'accès à des documents ou à des pages extérieures doit donc se protéger autrement, en séparant les données des consignes, en limitant les droits des outils et en gardant une validation humaine avant toute action irréversible.

Ces conclusions ont leurs limites. Les mesures viennent d'un seul portable sans GPU, avec cent exemples par classe, ce qui donne des intervalles de confiance de quelques points. Lakera Guard et Prompt-Guard n'ont pas pu être mesurés faute d'accès. La méthode est rejouable en une commande, sur CPU, sur Colab ou avec Docker, ce qui permet de refaire la comparaison quand les outils évolueront, et ils évoluent vite.
