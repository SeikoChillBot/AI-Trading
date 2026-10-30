# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.56 % rendement net moyen, 2.80 points face au Hold, -3.86 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.40 % rendement net moyen, 5.40 points face au Hold, 5.08 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.92 % rendement net moyen, -0.03 points face au Hold, -8.91 % avec frais doublés, 16 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés en tendance** : Simuler une période de 7 jours en position longue spot sans levier sur BTCUSD avec un capital fictif de 20 USD en appliquant des frais de transaction doublés. Critère d'abandon : L'hypothèse est réfutée si la performance nette dépasse celle du témoin Hold malgré le doublement des frais.
- **SOLUSD — Validation prospective d'un seuil de breakout** : Observer un placement fictif long spot sans levier de 20 USD sur SOLUSD pendant 3 jours lors d'un mouvement de marché classé comme sampled_large_transfer ou market_selloff. Critère d'abandon : L'hypothèse est réfutée si le drawdown dépasse celui observé sur la même période par le robot témoin de référence.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
