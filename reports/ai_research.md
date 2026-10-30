# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.08 % rendement net moyen, 2.66 points face au Hold, -4.45 % avec frais doublés, 8 trades clôturés, drawdown maximal 19.51 % sur 7 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 8.38 % rendement net moyen, 4.88 points face au Hold, 5.99 % avec frais doublés, 6 trades clôturés, drawdown maximal 25.17 % sur 7 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.49 % rendement net moyen, -0.03 points face au Hold, -8.59 % avec frais doublés, 14 trades clôturés, drawdown maximal 35.01 % sur 7 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés** : Simuler 20 USD en position long spot sur 3 jours en période de selloff avec des frais doublés pour observer l'impact direct sur le rendement net. Critère d'abandon : Rejeter l'hypothèse si le rendement net dépasse ou égale le témoin Hold dans plus de la moitié des fenêtres testées.
- **ETHUSD — Impact d'un rebond sur le sentiment de marché bas** : Placer un test fictif de 20 USD sur 1 jour lors d'une phase de market_selloff échantillonnée pour mesurer l'écart par rapport au maintien. Critère d'abandon : Rejeter l'hypothèse si l'excès de rendement par rapport au Hold reste négatif de plus de 2 points.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
