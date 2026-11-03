# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.40 % rendement net moyen, 2.74 points face au Hold, -4.95 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 4.88 % rendement net moyen, 5.83 points face au Hold, 2.20 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, drawdown_below_20_pct.
- SOLUSD : -5.45 % rendement net moyen, 0.45 points face au Hold, -9.62 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais doublés et seuil de rupture** : Rejouer la stratégie breakout BTCUSD sur de nouvelles données futures non vues en appliquant un coût de transaction doublé. Critère d'abandon : Si le rendement net prospectif avec frais doublés dépasse la borne inférieure historique sans amélioration du drawdown, l'hypothèse est réfutée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
