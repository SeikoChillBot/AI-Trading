# AIT — Recherche cumulative de stratégies (29 octobre 2026)

## Mission
Le laboratoire doit rechercher des **logiques de trading testables** et apprendre des hypothèses rejetées, pas seulement commenter les rendements des 36 robots. Aucun résultat financier n'est garanti.

## Architecture mise en place
- `research/market_knowledge.py` : conserve jusqu'à 365 journées UTC d'indicateurs publics source-qualifiés, sans fabriquer d'historique manquant. Ces relevés ne sont pas encore un jeu d'entraînement de signal fiable.
- `research/strategy_foundry.py` : Gemini peut proposer jusqu'à deux hypothèses par réponse, sous forme de règles bornées (tendance, retour à la moyenne, cassure ; paramètres autorisés sur BTC/ETH/SOL). Des références déterministes restent actives en absence de proposition IA. Aucun code arbitraire généré n'est exécuté.
- `state/strategy_knowledge_base.json` : archive dédoublonnée des hypothèses, version des règles, résultats de replay et contrôles échoués. La mémoire est relue aux cycles Gemini suivants par `research/ai_reflection.py` / `research/ai_decision_support.py`.
- `research/strategy_forward.py` : photographie les règles figées et suit les **nouvelles** bougies journalières, sans reconstruire rétroactivement des ordres. Chaque expérience utilise 20 USD fictifs et conserve une comparaison à l'achat-conservation. Il faut plusieurs jours et transactions futures avant toute discussion de robustesse.
- `build_site.py` + `site/lab04-research.js` : présentent les idées, leur provenance et les limites dans le Journal IA, sans changer les cinq onglets ni les portefeuilles d'origine.

## Validation et garde-fous
- Comparaisons historiques sur six fenêtres chronologiques avec frais de 0,9 % par côté, frais doublés, témoins Hold, drawdown et nombre de transactions. **Exploration seulement :** Gemini a déjà pu lire des résumés des mêmes prix ; ce n'est pas un véritable échantillon vierge.
- Le suivi prospectif utilise un signal construit sur la clôture précédente, un prix d'ouverture observé ultérieurement et une valorisation après frais. Ce n'est pas l'exécution réelle sur un carnet et ne reproduit pas parfaitement les glissements de marché.
- Rien ne modifie les 36 historiques, les 12 robots Hold témoins, les clés d'échange, les paramètres d'ordres réels ni la facturation OpenAI. Aucun modèle payant ajouté.
- Gemini peut soumettre une hypothèse ; **seul Python valide la grammaire et exécute les essais isolés**. Aucune promotion automatique issue de ce nouvel atelier.
- Tests hors ligne : `tests/test_strategy_foundry.py`, `tests/test_market_knowledge.py`, `tests/test_strategy_forward.py`. Le workflow recherche exécute ces tests avant les collectes.

## État observé à 18:55 UTC le 29/10
Le workflow recherche `40935221049` a réussi avec les 7 tests de la stratégie fondatrice et trois références exploratoires : BTC tendance −5,1358 %, ETH retour à la moyenne −17,048 %, SOL cassure −0,2376 % de moyenne historique. **Aucune ne passe l'ensemble des critères.** Gemini a effectivement répondu, mais la sortie vérifiée ne contenait pas encore de nouvelle stratégie structurée (`strategy_designs=0`). Le cycle a commencé avant l'intégration complète du suivi prospectif ; ce dernier et l'historique des caractéristiques de marché doivent encore être vérifiés dans un cycle de recherche suivant.

## Suite technique
1. Vérifier un cycle complet sur le nouveau workflow, publication des fichiers market_knowledge et strategy_forward, ainsi que leurs tests.
2. Vérifier le premier vrai `strategy_designs` provenant de Gemini, puis son archivage et son suivi séparé ; ne pas confondre idée Gemini et référence quantitative.
3. Étendre progressivement la grammaire seulement avec source de données, frais, preuve de qualité, tests de non-régression et validation future indépendante.
4. Quand le nombre de journées accumulées sera significatif, étudier les régimes de marché ; ne pas inventer une corrélation prédictive sur quelques jours.
