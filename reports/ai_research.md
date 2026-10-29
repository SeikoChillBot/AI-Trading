# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.67 % rendement net moyen, 0.83 points face au Hold, -5.35 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 7.83 % rendement net moyen, 4.33 points face au Hold, 5.51 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.22 % rendement net moyen, -2.53 points face au Hold, -9.02 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés sur BTC** : Rejouer l'ensemble des historiques OOS en appliquant des frais de transaction multipliés par 2 sur les robots BTC sans modifier les fenêtres. Critère d'abandon : Si le rendement net moyen reste positif après doublement des frais, l'hypothèse de sensibilité est rejetée.
- **ETHUSD — Validation prospective post-drawdown sur ETH** : Collecter 30 nouvelles observations de forward paper trading sans réajuster les paramètres et mesurer l'apparition de nouveaux drawdowns maximaux. Critère d'abandon : Si le nouveau drawdown maximal reste inférieur au pire drawdown historique sans dépassement, l'hypothèse est rejetée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
