# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.66 % rendement net moyen, 2.69 points face au Hold, -5.20 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 4.57 % rendement net moyen, 5.78 points face au Hold, 1.89 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.61 % rendement net moyen, 0.05 points face au Hold, -9.78 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés** : Rejouer l'ensemble des signaux BTCUSD avec des coûts de transaction doublés sur une période out-of-sample indépendante. Critère d'abandon : L'expérience est réfutée si la baisse de rendement net dépasse strictement le double de l'augmentation des frais de transaction.
- **ETHUSD — Filtre de volatilité pour la réduction des faux signaux** : Simuler une règle de breakout filtrée par une volatilité historiquement faible sur ETHUSD sur de nouvelles données futures. Critère d'abandon : L'hypothèse est rejetée si le nombre de trades chute de plus de 50 pour cent sans amélioration mesurable du ratio de rendement net par rapport au témoin hold.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
