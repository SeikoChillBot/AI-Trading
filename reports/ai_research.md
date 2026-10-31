# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.72 % rendement net moyen, 3.03 points face au Hold, -4.24 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.30 % rendement net moyen, 5.73 points face au Hold, 4.79 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.29 % rendement net moyen, 0.38 points face au Hold, -8.12 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés** : Exécuter en simulation un test de 20 USD sur BTCUSD en spot long pendant 7 jours en conditions de frais doublés, en comparant la trajectoire au témoin Hold. Critère d'abandon : Rejeter l'hypothèse si la performance nette dépasse le seuil du témoin Hold sous les mêmes contraintes de frais.
- **ETHUSD — Évaluation de la sensibilité au repli du marché** : Lancer une simulation de placement fictif de 20 USD sur ETHUSD pendant 3 jours lors d'un scénario de repli de marché échantillonné. Critère d'abandon : Invalider l'hypothèse si le drawdown maximal reste inférieur à celui enregistré par le robot témoin eth_hold sur la même période.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
