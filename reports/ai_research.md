# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.40 % rendement net moyen, 2.74 points face au Hold, -4.95 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 4.88 % rendement net moyen, 5.83 points face au Hold, 2.20 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, drawdown_below_20_pct.
- SOLUSD : -5.45 % rendement net moyen, 0.45 points face au Hold, -9.62 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés pour BTC** : Rejouer l'historique des ordres avec des frais doublés et comparer le rendement net final à la configuration de base. Critère d'abandon : Si le rendement net ne change pas ou si le nombre de trades varie alors que la règle de signal est identique, l'hypothèse est réfutée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
