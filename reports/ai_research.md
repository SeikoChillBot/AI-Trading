# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_failed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -3.40 % rendement net moyen, 2.69 points face au Hold, -6.29 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 2.09 % rendement net moyen, 7.07 points face au Hold, -0.52 % avec frais doublés, 7 trades clôturés, drawdown maximal 23.14 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.
- SOLUSD : -3.92 % rendement net moyen, 2.82 points face au Hold, -7.90 % avec frais doublés, 14 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Contrôler la robustesse historique de BTCUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.
- **ETHUSD — Contrôler la robustesse historique de ETHUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.
- **SOLUSD — Contrôler la robustesse historique de SOLUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
