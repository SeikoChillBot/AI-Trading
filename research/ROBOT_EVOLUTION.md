# Seiko Trading Lab — évolution autonome des 36 robots

Mise à jour : 28 octobre 2026. **Simulation fictive exclusivement.**

## Objectif
Maximiser les rendements **nets de frais et à risque borné**, sans promesse de rentabilité. Gemini examine les statistiques et peut proposer jusqu'à trois ajustements ciblés par analyse (au plus quatre analyses IA par jour UTC). Les stratégies des 36 robots ne sont pas remplacées par du code généré par le modèle.

## Robots éligibles
- 15 robots crypto utilisent un multiplicateur de sensibilité des signaux d'entrée, conservant leurs modes d'origine.
- 9 robots multi-actifs `trend20` peuvent adapter la sensibilité aux entrées/sorties.
- Les **12 robots Hold** restent des témoins immuables pour mesurer la valeur ajoutée. Ensemble : 36 robots.
- Paramètres autorisés : `entry_scale=0.8` (plus réactif), `1.0` (origine) ou `1.2` (plus prudent). Une réponse IA ne peut proposer que `0.8` ou `1.2`; tous les autres paramètres et toute modification de code sont rejetés. Pas de leverage, pas de short ni d'ordres réels.

## Chaîne autonome
1. Le workflow `research.yml` actualise les études de marché, l'analyse Gemini et le fichier `reports/ai_research_proposals.json`.
2. Gemini peut recommander dans `bot_adjustments` un identifiant de robot reconnu, le profil prudent ou réactif et une justification. C'est **une hypothèse**, pas une validation.
3. `research/robot_evolution.py` ouvre un candidat audité en `state/robot_evolution_state.json` sans toucher à la stratégie existante.
4. Les appels réguliers de `bot.py` et `multi_asset_sim.py` alimentent `research/robot_shadow.py`, qui simule prospectivement le **candidat, le réglage témoin et le scénario frais doublés** avec des positions fictives séparées. Les nouveaux historiques ne sont jamais reconstruits à rebours.
5. Le workflow de recherche vérifie les critères minimaux : **14 jours crypto / 30 jours multi-actifs**, au moins **20 allers-retours clôturés**, au moins 120/24 observations futures, rendement net candidat positif et supérieur de **2 points de pourcentage** au témoin, rendement positif avec frais doublés, drawdown inférieur ou égal à **15 %** et non supérieur au témoin. Aucun rendement futur n'est garanti.
6. Si et seulement si tous les critères sont remplis, `state/robot_tuning_active.json` reçoit un réglage borné audité ; `bot.py`, `realistic_sim.py` et `multi_asset_sim.py` l'utilisent lors des futures décisions. Les anciennes transactions et valorisations restent préservées.
7. Le shadow continue et revient automatiquement au réglage initial si, après au moins deux jours supplémentaires, le candidat sous-performe significativement (au moins 4 points) ou si son drawdown atteint 25 %.

## Transparence sur la qualité des preuves
Les simulations shadow utilisent une approximation avec cotation **clôturée observée ultérieurement** et frais modélisés, sans vrai carnet d'ordres pour chaque décision ; cela n'est **pas une preuve d'exécution chez un courtier**. Certains marchés multi-actifs reposent sur des cotations publiques non officielles, et EURUSD sur une référence BCE non exécutable. Les contrôles montrent des conditions nécessaires à une expérience de paper trading, pas un conseil ou une garantie de rendement. Si une source manque ou qu'il n'y a pas assez de transactions, le réglage d'origine est conservé.

## Journal visuel
Dans `https://seikochillbot.github.io/AI-Trading/` > **Analyse** > **Évolution autonome des robots** :
- 36 fiches individuelles (36 suivis, 12 témoins Hold).
- Données actuelles : rendement de simulation, nombre d'observations, nombre de transactions clôturées.
- Raison Gemini, proposition de sensibilité, statut (observation/en test/activée/retour arrière), critères non remplis.
- Historique chronologique des propositions et activations dans `reports/robot_evolution_events.jsonl`.

Les fichiers `state/robot_tuning_active.json`, `state/robot_evolution_state.json`, `state/robot_shadow_state.json` et `reports/` doivent être conservés entre les exécutions GitHub. Ne jamais remettre à zéro les portefeuilles originaux.
