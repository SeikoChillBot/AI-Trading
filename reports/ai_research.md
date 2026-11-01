# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.79 % rendement net moyen, 2.97 points face au Hold, -4.34 % avec frais doublés, 8 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.14 % rendement net moyen, 6.46 points face au Hold, 4.63 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, drawdown_below_20_pct.
- SOLUSD : -5.48 % rendement net moyen, -0.16 points face au Hold, -9.24 % avec frais doublés, 14 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Stress de résilience aux frais sur BTC** : Simuler le comportement du robot btc_scalp_conservative avec des frais réels majorés de 100 % sur de nouvelles données entrantes. Critère d'abandon : Rejeter l'hypothèse si le rendement net devient inférieur au témoin Hold dans plus de 50 pour cent des fenêtres de test.
- **ETHUSD — Comparaison de filtrage par volatilité sur ETH** : Exécuter une simulation prospective de 3 jours sur ETHUSD avec un filtre de volatilité calme obligatoire avant toute entrée. Critère d'abandon : Rejeter l'hypothèse si le drawdown maximum dépasse celui de la stratégie de référence sans filtre sur la même période.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
