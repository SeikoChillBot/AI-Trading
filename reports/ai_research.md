# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_failed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.76 % rendement net moyen, 6.15 points face au Hold, -4.08 % avec frais doublés, 8 trades clôturés, drawdown maximal 16.10 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 1.61 % rendement net moyen, 9.88 points face au Hold, -0.61 % avec frais doublés, 7 trades clôturés, drawdown maximal 18.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_with_double_costs.
- SOLUSD : -4.36 % rendement net moyen, 4.41 points face au Hold, -7.47 % avec frais doublés, 12 trades clôturés, drawdown maximal 22.24 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Contrôler la robustesse historique de BTCUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.
- **ETHUSD — Contrôler la robustesse historique de ETHUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.
- **SOLUSD — Contrôler la robustesse historique de SOLUSD** : Comparer le témoin Hold, les frais actuels et doublés, puis attendre des données prospectives jamais utilisées pour choisir les seuils. Critère d'abandon : Rejeter si la performance nette ou la résistance aux frais ne s'améliore pas hors échantillon.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
