# Cycle de vie des robots : refonte progressive (proposition, 2026-11-11)

## Constat et données
Le rapport `reports/robot_evolution.json` du 2026-11-11T15:15:46Z conserve 36 robots, dont 12 témoins Hold immuables et 24 robots en phase de proposition. Des pertes nettes et drawdowns importants justifient un audit des hypothèses initiales, **pas** une affirmation qu'un robot ne pourra jamais récupérer. Le rapport `reports/strategy_forward.json` du même jour indique 31 pistes suivies, 6 essais archivés et aucune piste avec preuve prospective suffisante.

## Phase 1 : transparence, sans modifier les simulations
La rubrique de recherche du site affiche une liste **diagnostique** des robots avec rendement papier <= -30 %, drawdown >= 30 % et >= 20 opérations clôturées. Ces seuils ne sont **pas** des critères de suppression ni des tests de significativité. Les témoins Hold sont exclus. Aucune donnée historique, aucun robot et aucun paramètre n'est modifié.

## Phase 2 : sélection scientifique à développer
- Comparer chaque robot à son Hold, sur les **mêmes périodes**, après frais, spreads et glissement; mesurer le rendement net, le drawdown, le turnover, le nombre de trades et la sensibilité aux frais doublés.
- Identifier des régimes observables avec des données datées (tendance, volatilité, liquidité et mouvements importants), sans déduire qu'un transfert important est un ordre de marché.
- Gemini ou GPT peuvent rédiger des hypothèses **déclaratives, bornées, réfutables**; le code local valide les paramètres et les exécute uniquement en simulation indépendante, avec au maximum 20 USD théoriques par scénario.
- Préenregistrer l'hypothèse, sa date, le benchmark et les règles de rejet avant l'évaluation prospective; éviter le réemploi des mêmes données pour sélectionner puis prouver.
- Conserver les pistes suffisamment longtemps pour observer plusieurs régimes et un échantillon de transactions réellement clôturées. Une performance nulle sans transaction n'est pas un avantage.
- Ne qualifier une nouvelle stratégie qu'après tests prospectifs appariés, sensibilité aux frais, drawdown maîtrisé et contrôle de couverture. En cas de données insuffisantes, statut « non concluant ».

## Phase 3 : archivage et remplacement à développer
Ne jamais supprimer les 36 identités et historiques initiaux ni les 12 témoins Hold. Distinguer :
1. **Historique immuable** : tous les résultats originaux restent accessibles.
2. **Version active en simulation** : peut être désactivée seulement après une décision vérifiable.
3. **Version candidate** : stratégie nouvelle, isolée du portefeuille historique.
4. **Version archivée** : paramètres, dates, motifs, preuves, résultats et identifiant du successeur sont conservés; l'archivage est réversible et ne réécrit jamais les résultats passés.

Pour toute promotion, afficher dans le site : robot/version, source de l'hypothèse (Gemini/GPT/statistique), observations horodatées, régime, résultats appariés net/Hold, frais, drawdown, robustesse, décision, justification, date, et éventuel retour arrière. Les promotions ne sont **pas** autorisées par cette première phase.

## Points de contrôle
- Aucune promesse de rentabilité, aucun argent réel, aucune API GPT payante.
- Aucun ajustement automatique sur une simple perte ou un score historique.
- Le tableau « candidats à réexaminer » n'est pas une preuve de stratégie définitivement perdante.
- La création d'un registre de versions et d'un moteur de remplacement sera une PR distincte, testée et auditée avant activation.
