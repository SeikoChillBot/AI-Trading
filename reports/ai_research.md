# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.67 % rendement net moyen, 0.83 points face au Hold, -5.35 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 7.83 % rendement net moyen, 4.33 points face au Hold, 5.51 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.22 % rendement net moyen, -2.53 points face au Hold, -9.02 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés** : Rejouer les signaux de btc_momentum avec des frais augmentés de 100 pour cent sur des données journalières historiques non utilisées. Critère d'abandon : Rejeter l'hypothèse si la perte nette moyenne reste inférieure à 2 pour cent sur la période.
- **ETHUSD — Robustesse des seuils de repli** : Évaluer eth_reversion sur trois fenêtres OOS disjointes de 30 jours en enregistrant le drawdown maximal. Critère d'abandon : Rejeter l'hypothèse si le drawdown reste strictement inférieur à 3 pour cent sur toutes les fenêtres.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
