# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_failed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.22 % rendement net moyen, 5.94 points face au Hold, -4.75 % avec frais doublés, 9 trades clôturés, drawdown maximal 16.10 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 1.62 % rendement net moyen, 10.13 points face au Hold, -0.59 % avec frais doublés, 7 trades clôturés, drawdown maximal 18.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_with_double_costs.
- SOLUSD : -7.13 % rendement net moyen, 2.03 points face au Hold, -10.83 % avec frais doublés, 16 trades clôturés, drawdown maximal 26.36 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Contrôler la robustesse historique de BTCUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.
- **ETHUSD — Contrôler la robustesse historique de ETHUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.
- **SOLUSD — Contrôler la robustesse historique de SOLUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
