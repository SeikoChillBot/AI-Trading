# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -3.76 % rendement net moyen, 1.22 points face au Hold, -6.67 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 4.97 % rendement net moyen, 5.36 points face au Hold, 2.30 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.18 % rendement net moyen, -0.31 points face au Hold, -9.40 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais sur breakout** : Simuler l'exécution d'un robot breakout sur BTCUSD avec des frais normaux et doublés sur 7 jours de données forward non encore intégrées au moteur d'optimisation. Critère d'abandon : Si le rendement net après frais doublés chute de plus de 50% par rapport à la base de référence, l'hypothèse de robustesse aux coûts est rejetée.
- **ETHUSD — Filtre de volatilité sur réversion RSI** : Observer le comportement du robot rsi_reversal sur ETHUSD sur 3 jours avec un filtre de volatilité désactivé versus activé, sans modifier la taille des positions. Critère d'abandon : Si le nombre de trades fructueux n'augmente pas tout en conservant un drawdown inférieur au témoin hold, l'hypothèse est réfutée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
