# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.79 % rendement net moyen, 2.97 points face au Hold, -4.34 % avec frais doublés, 8 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.14 % rendement net moyen, 6.46 points face au Hold, 4.63 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, drawdown_below_20_pct.
- SOLUSD : -5.48 % rendement net moyen, -0.16 points face au Hold, -9.24 % avec frais doublés, 14 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés et seuil de déclenchement** : Simuler un placement fictif de 20 USD en long spot sans levier sur BTCUSD pendant 3 jours lors d'un signal de type sampled_large_transfer, en appliquant des frais normaux et doublés. Critère d'abandon : Rejeter l'hypothèse si le rendement net prospectif après frais doublés reste négatif ou sous-performe le Hold témoin sur la même période.
- **ETHUSD — Validation prospective du retour à la moyenne sur fenêtres courtes** : Simuler un placement fictif de 20 USD en long spot sans levier sur ETHUSD pendant 7 jours en condition market_selloff. Critère d'abandon : Rejeter l'hypothèse si le drawdown dépasse 15 % ou si la performance nette est inférieure au témoin d'achat-conservation.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
