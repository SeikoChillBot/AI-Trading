# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.79 % rendement net moyen, 2.97 points face au Hold, -4.34 % avec frais doublés, 8 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.14 % rendement net moyen, 6.46 points face au Hold, 4.63 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, drawdown_below_20_pct.
- SOLUSD : -5.48 % rendement net moyen, -0.16 points face au Hold, -9.24 % avec frais doublés, 14 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés et surcoûts** : Rejouer la stratégie breakout BTCUSD avec un niveau de frais multiplié par deux sur 81 périodes forward, en comparant les résultats nets au témoin Hold. Critère d'abandon : Si le rendement net après frais doublés dépasse la performance du témoin Hold sur la même période, l'hypothèse de vulnérabilité est réfutée.
- **ETHUSD — Évaluation de la réversibilité de la tendance et seuils** : Simuler une exécution spot long sans levier sur 7 jours avec la stratégie de réversion, en comparant la fréquence de trade et le drawdown. Critère d'abandon : Si le robot dépasse le rendement du Hold avec un drawdown inférieur à 10% sur les données prospectives, l'hypothèse d'échec de la réversion est rejetée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
