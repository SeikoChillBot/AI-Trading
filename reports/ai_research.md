# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.67 % rendement net moyen, 0.83 points face au Hold, -5.35 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 7.83 % rendement net moyen, 4.33 points face au Hold, 5.51 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.22 % rendement net moyen, -2.53 points face au Hold, -9.02 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance des coûts de transaction doublés** : Rejouer l'ensemble des signaux historiques et OOS de BTCUSD en appliquant des frais majorés de 100 % sur une fenêtre de 7 jours avec 20 USD fictifs. Critère d'abandon : Si le rendement net moyen reste strictement supérieur à celui de la configuration initiale sous double coût, l'hypothèse de sensibilité est rejetée.
- **ETHUSD — Simulation de tendance sur 3 jours post-transfert stablecoin** : Observer le comportement de l'actif ETHUSD sur une période de 3 jours consécutifs suite à l'enregistrement de transferts notables de l'échantillon. Critère d'abandon : Si la performance cumulée dépasse le témoin hold de plus de 2 points sur l'horizon testé, l'hypothèse est réfutée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
