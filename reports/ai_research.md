# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -3.90 % rendement net moyen, 1.87 points face au Hold, -6.81 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 5.18 % rendement net moyen, 6.37 points face au Hold, 2.51 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.60 % rendement net moyen, 0.60 points face au Hold, -8.86 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais sur breakout** : Rejouer la stratégie breakout avec des frais doublés sur des données de bougies futures non encore analysées. Critère d'abandon : Si le rendement net après frais doublés reste supérieur ou égal aux performances historiques sans coûts additionnels, l'hypothèse est réfutée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
