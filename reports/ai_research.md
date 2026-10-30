# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.56 % rendement net moyen, 2.80 points face au Hold, -3.86 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.40 % rendement net moyen, 5.40 points face au Hold, 5.08 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.92 % rendement net moyen, -0.03 points face au Hold, -8.91 % avec frais doublés, 16 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Sensibilité aux frais et résistance du momentum** : Simuler l'exécution des ordres de btc_momentum avec des frais doublés sur 7 jours consécutifs hors échantillon. Critère d'abandon : Rejeter l'hypothèse si la performance nette de la variante à frais doublés devient inférieure au témoin Hold sur la même période.
- **ETHUSD — Filtre de volatilité et réduction des faux signaux** : Observer en paper trading sur 3 jours le comportement d'ETHUSD avec le filtre actif par rapport à la version standard. Critère d'abandon : Rejeter l'hypothèse si le nombre de trades non rentables augmente ou si le drawdown dépasse celui de la version de référence.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
