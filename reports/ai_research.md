# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.72 % rendement net moyen, 3.03 points face au Hold, -4.24 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.30 % rendement net moyen, 5.73 points face au Hold, 4.79 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.29 % rendement net moyen, 0.38 points face au Hold, -8.12 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais de transaction sur BTCUSD** : Rejouer exactement les signaux de btc_momentum et btc_breakout avec des frais doublés en simulation prospective sur une fenêtre de 3 jours. Critère d'abandon : Si le rendement net après doublement des frais dépasse ou égale le scénario de référence sans frais, l'hypothèse de sensibilité aux coûts est réfutée.
- **ETHUSD — Évaluation du positionnement de retour à la moyenne (mean reversion) sur ETHUSD** : Suivi en simulation sur 7 jours de eth_reversion en comparant strictement sa trajectoire nette au témoin eth_hold. Critère d'abandon : Si le robot dépasse le rendement du témoin hold avec un drawdown inférieur à 8.5% sur la période, l'hypothèse d'inefficacité est rejetée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
