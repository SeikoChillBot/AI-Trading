# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.72 % rendement net moyen, 3.03 points face au Hold, -4.24 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.30 % rendement net moyen, 5.73 points face au Hold, 4.79 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.29 % rendement net moyen, 0.38 points face au Hold, -8.12 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés** : Simuler l'exécution des signaux BTCUSD avec des frais doublés sur les prochaines observations de marché pour mesurer l'impact net par rapport au témoin Hold. Critère d'abandon : Rejeter l'hypothèse si la perte nette dépasse celle du modèle à frais normaux de plus de deux points de pourcentage.
- **ETHUSD — Filtre de volatilité pour le retour à la moyenne** : Observer le comportement de la stratégie ETHUSD sous contrainte de volatilité calme sur de nouvelles données journalières. Critère d'abandon : Rejeter l'hypothèse si le drawdown dépasse celui observé sur la période précédente.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
