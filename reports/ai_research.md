# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.66 % rendement net moyen, 2.69 points face au Hold, -5.20 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 4.57 % rendement net moyen, 5.78 points face au Hold, 1.89 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.61 % rendement net moyen, 0.05 points face au Hold, -9.78 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Sensibilité aux frais et filtrage de volatilité sur BTC** : Rejouer la stratégie breakout sur BTCUSD avec les frais actuels et des frais doublés en collectant de nouvelles données journalières non utilisées. Critère d'abandon : Rejeter l'hypothèse si le rendement net avec frais doublés chute de plus de 2% supplémentaires sans réduction proportionnelle du drawdown maximal.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
