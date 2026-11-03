# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.40 % rendement net moyen, 2.74 points face au Hold, -4.95 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 4.88 % rendement net moyen, 5.83 points face au Hold, 2.20 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, drawdown_below_20_pct.
- SOLUSD : -5.45 % rendement net moyen, 0.45 points face au Hold, -9.62 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Impact de la volatilité active sur le breakout** : Exécuter un placement fictif de 20 USD sur BTCUSD en long spot sans levier pendant 3 jours lors d'un motif market_selloff en comparant le rendement net avec et sans le filtre de volatilité sur de nouvelles données futures. Critère d'abandon : Rejeter l'hypothèse si le rendement net avec filtre devient inférieur au hold ou si les frais dépassent l'excès de rendement.
- **ETHUSD — Résilience des seuils de retour à la moyenne** : Tester un placement fictif de 20 USD sur ETHUSD en long spot sans levier pendant 7 jours lors d'un motif market_uptrend en augmentant le seuil de déclenchement. Critère d'abandon : Rejeter l'hypothèse si le nombre de roundtrips tombe à zéro ou si le drawdown dépasse celui de la configuration de base.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
