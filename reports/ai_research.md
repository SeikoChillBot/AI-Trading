# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.03 % rendement net moyen, 2.61 points face au Hold, -4.57 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 6.06 % rendement net moyen, 5.98 points face au Hold, 3.56 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.24 % rendement net moyen, 0.18 points face au Hold, -9.25 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés** : Rejouer l'ensemble des signaux BTCUSD avec des frais doublés en simulation sur les données de forward paper pour observer la dégradation du rendement net. Critère d'abandon : Si la baisse du rendement net dépasse 50% de la performance initiale ou si le nombre d'ordres tombe à zéro, l'hypothèse est rejetée.
- **ETHUSD — Filtre de volatilité active sur ETHUSD** : Simuler une variante de stratégie breakout avec le filtre active_volatility sur une fenêtre prospective de 7 jours avec un capital fictif de 20 USD. Critère d'abandon : Si le rendement net reste inférieur au témoin ETH_Hold sur la même période, l'hypothèse est rejetée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
