# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.67 % rendement net moyen, 0.83 points face au Hold, -5.35 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 7.83 % rendement net moyen, 4.33 points face au Hold, 5.51 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.22 % rendement net moyen, -2.53 points face au Hold, -9.02 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de placement fictif BTCUSD 7 jours** : Simuler un placement fictif de 20 USD en long spot sans levier sur BTCUSD pendant 7 jours en conditions de marché market_uptrend. Critère d'abandon : Le test sera rejeté si le rendement net est négatif à l'issue des 7 jours de simulation.
- **ETHUSD — Test de placement fictif ETHUSD 3 jours** : Simuler un placement fictif de 20 USD en long spot sans levier sur ETHUSD pendant 3 jours en conditions de marché market_selloff. Critère d'abandon : Le test sera rejeté si le drawdown dépasse 3 % pendant la période de simulation.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
