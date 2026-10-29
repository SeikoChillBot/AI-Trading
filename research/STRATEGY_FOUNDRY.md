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

## Boucle d'auto-optimisation (29/10/2026)

**Mission retenue par Seiko :** AIT recherche de manière autonome de nouvelles configurations, conserve ses échecs et ses résultats, et n'autorise l'idée d'un essai en argent réel qu'après des validations prospectives et un consentement explicite. Le profit ne peut être garanti ni « optimisé jusqu'à réussite » par la seule recherche répétée.

### Modules ajoutés
- `research/autonomous_optimizer.py` : explore automatiquement chaque semaine de nouveaux jeux de paramètres sur BTC/ETH/SOL, à partir d'une **grille bornée** de logiques déjà définies (tendance, retour à la moyenne, cassure ; fenêtres 10/20/40 jours ; seuils 0,5/1/2 % ; détention 1/3/7 jours). Choisit sur 4 fenêtres anciennes de 60 jours, puis évalue **après sélection** sur 2 fenêtres historiques ultérieures. Cette seconde période est un contrôle chronologique réutilisé, **pas** un test véritablement vierge : les données de marché ont déjà servi à d'autres recherches.
- Optimisation d'un score qui privilégie le rendement **net après frais**, pénalise la baisse maximale et les pertes avec frais doublés, tient compte du témoin achat-conservation et pénalise le manque de transactions. Aucun mécanisme de « chasse au rendement positif » par falsification de résultats.
- `reports/autonomous_optimizer.json` / `state/autonomous_optimizer.json` : découvertes datées et candidates figées ; cadence de recherche bornée, pas de nouvelle expérience chaque relance GitHub.
- `research/strategy_foundry.py` reçoit les meilleures candidates de recherche **dans un laboratoire isolé** et ajoute leurs traces à la mémoire cumulative ; `research/strategy_forward.py` observe uniquement les nouvelles bougies après leur inscription. Gemini reçoit les conclusions compactes de ce moteur dans le contexte de ses prochains appels, sans appel API supplémentaire.
- `research/manual_live_review.py` : contrôle **humain uniquement**, aucun ordre réel. Il exige des données prospectives suffisantes (au moins 90 nouvelles journées, au moins 10 transactions clôturées), un gain net fictif d'au moins 2 %, un excédent positif face au témoin, un drawdown maximal de 10 %, des tests historiques résistants à des frais doublés et des preuves fraîches. Même s'ils passent, les critères ne donnent qu'un statut de **candidat à l'examen humain**, jamais une autorisation de déposer des fonds.
- La vraie phase financière nécessitera en plus un lieu d'exécution clairement choisi, ses minimums d'ordres/frais, des essais de réconciliation d'ordres, une limite absolue de perte, un arrêt d'urgence, l'absence de levier et une validation spécifique de l'utilisateur. **Aucune connexion à un échange ni aucun achat réel sont implémentés.**
- Le tableau de bord `Journal IA` expose les candidats du moteur et la porte de revue humaine sans nouvel onglet. Les 36 robots d'origine, 12 Hold témoins et historiques ne sont pas modifiés par les nouveaux modules.
- Tests automatisés : `tests/test_autonomous_optimizer.py`, `tests/test_manual_live_review.py`, plus tous les tests précédents. Le workflow `.github/workflows/research.yml` appelle désormais le moteur d'optimisation **avant Gemini**, puis la foundry, le suivi prospectif et enfin le contrôle manuel. Les résultats sont sauvegardés via GitHub Actions.

### Honnêteté et prochaines limites
- Il reste à vérifier un **nouveau cycle réel** sous le workflow complété et les rapports correspondants. Des commits GitHub réussis ne prouvent pas la réussite de GitHub Actions.
- Le moteur ne découvre pas encore des logiques sans limites : les règles disponibles restent une grille finie, sans apprentissage neuronal entraîné sur la série financière.
- Les backtests peuvent être surajustés, surtout si Gemini voit leurs résumés. Une performance prospective robuste et une analyse de qualité d'exécution restent indispensables avant d'envisager le réel.

## Évolution autonome et compétition fictive — extension du 29/10/2026

Objectif : rendre le moteur d'AIT capable d'explorer davantage de familles de règles, de conserver les erreurs et de poursuivre les expérimentations sur la durée, sans faire passer les simulations pour des profits futurs.

### Nouveaux blocs réellement intégrés
- **Sept logiques de signaux au total**, toutes basées sur les cours clôturés : `trend_following`, `mean_reversion`, `breakout`, `ema_trend`, `rsi_reversal`, `volatility_gate`, `dual_confirmation`. RSI, EMA, filtre de volatilité et double confirmation s'ajoutent aux trois logiques de référence. Le moteur d'analyse Gemini peut soumettre ces noms uniquement comme des règles déclaratives, sans écrire ni exécuter de Python.
- `research/strategy_evolution.py` : génère chaque semaine, si de **nouvelles clôtures journalières** sont disponibles, un voisin de paramétrage sur chacun des trois actifs, avec identifiant stable, géniteur connu, dimension mutée et raisons historiques des échecs. Les comparaisons classent leurs configurations sur les **quatre fenêtres anciennes de développement** uniquement ; les deux fenêtres de contrôle sont lues après le classement. Une génération peut prendre une variante antérieure pour parent si sa performance historique de développement surpasse celle de l'optimiseur de référence. **Ce processus reste heuristique, fini et sujet au surajustement.**
- `research/strategy_foundry.py` reconnaît l'origine `bounded_evolution` de façon séparée de `gemini_structured_hypothesis` et `autonomous_grid_search`. Archives maximales : 80 hypothèses en cours de recherche, dédoublonnées.
- `research/strategy_competition.py` : classement et archivage prospectif exclusivement à partir de l'état fictif gelé. Le terme **championne fictive** exige au moins 120 nouvelles journées observées, 12 transactions clôturées, 2 % de rendement net après frais, un excédent positif par rapport au témoin Hold, moins de 10 % de drawdown, les tests historiques réussis ET 14 nouvelles journées successives satisfaisant les critères. Retrait du statut si les critères cessent d'être remplis. Ces seuils sont un écran prudent **et non une preuve statistique qu'une stratégie générera des gains** ; ne déploie aucun ordre réel et ne change aucun des 36 robots.
- `research/strategy_forward.py` : capacité active de 24 pistes, rotation conservatrice lors d'un encombrement en retenant les championnes fictives validées et en admettant les dernières idées ; archivage borné des anciennes pistes en `state/strategy_forward_positions.json`. Il ne crée jamais de faux ordres rétroactifs à partir de bougies manquantes.
- `research/ai_reflection.py` / `research/ai_decision_support.py` : Gemini peut lire des leçons limitées des mutations et de la compétition pour formuler ses prochaines hypothèses. Aucun nouvel appel IA payant, quota Gemini gratuit inchangé.
- Le Journal IA affiche désormais les compteurs d'évolution et de compétition fictive ; cinq onglets conservés.
- Nouveau contrôle CI isolé : `tests/test_strategy_evolution.py`, `tests/test_strategy_competition.py` et test de rotation `test_strategy_forward.py`, exécutés aussi par le workflow de recherche. Les tests de non-anticipation et d'absence d'accès au trading réel restent essentiels.

### Ce qui n'est PAS résolu par l'ajout de ces programmes
- Le moteur explore toujours **une grammaire finie**, à base de bougies quotidiennes essentiellement prix d'ouverture/clôture ; il n'invente pas librement des facteurs issus de volumes fiables, carnet d'ordres, financements, news ou transfert on-chain corrélés à des gains. Ces données devront être qualifiées et validées séparément avant d'en faire des signaux.
- La nouvelle base d'indicateurs accumule les observations au fil des jours ; elle ne reconstitue jamais un passé inexistant.
- Un premier déploiement ou un test de stratégie réussis n'est PAS une preuve prospective ; il faut des journées **futures** réellement observées et des transactions simulées pour discuter robustesse.
- Les classements ne constituent **aucun entraînement des poids de Gemini**. C'est de l'optimisation déterministe, une mémoire de décisions et une communication de feedback au modèle.
