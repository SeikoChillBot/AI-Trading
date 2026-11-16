# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_failed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -3.41 % rendement net moyen, 4.29 points face au Hold, -6.32 % avec frais doublés, 8 trades clôturés, drawdown maximal 16.04 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 2.05 % rendement net moyen, 8.94 points face au Hold, -0.39 % avec frais doublés, 6 trades clôturés, drawdown maximal 18.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_with_double_costs.
- SOLUSD : -5.58 % rendement net moyen, 4.04 points face au Hold, -9.25 % avec frais doublés, 13 trades clôturés, drawdown maximal 33.09 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Contrôler la robustesse historique de BTCUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.
- **ETHUSD — Contrôler la robustesse historique de ETHUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.
- **SOLUSD — Contrôler la robustesse historique de SOLUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
