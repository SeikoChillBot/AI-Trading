# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.79 % rendement net moyen, 2.97 points face au Hold, -4.34 % avec frais doublés, 8 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.14 % rendement net moyen, 6.46 points face au Hold, 4.63 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, drawdown_below_20_pct.
- SOLUSD : -5.48 % rendement net moyen, -0.16 points face au Hold, -9.24 % avec frais doublés, 14 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de placement fictif BTCUSD** : Simuler un placement fictif long spot de 20 USD sur BTCUSD pendant 3 jours en conditions de marché market_selloff, en collectant prospectivement les données sans réutiliser les holdouts. Critère d'abandon : Rejeter l'hypothèse si le rendement net final est inférieur au témoin Hold sur la même période de 3 jours.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
