# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.66 % rendement net moyen, 2.69 points face au Hold, -5.20 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 4.57 % rendement net moyen, 5.78 points face au Hold, 1.89 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.61 % rendement net moyen, 0.05 points face au Hold, -9.78 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance des frais et filtrage de volatilité** : Rejouer la stratégie BTCUSD avec les frais actuels et majorés de 50%, en comparant la fréquence des transactions et le drawdown résultant sur de nouvelles données futures. Critère d'abandon : L'expérience est rejetée si le rendement net avec frais majorés reste inférieur au témoin hold sur la même période.
- **ETHUSD — Évaluation comparative des seuils de réversion sur ETH** : Observer les performances prospectives d'ETHUSD sur 7 jours avec un profil ajusté et le comparer à l'actif témoin hold. Critère d'abandon : L'hypothèse est réfutée si l'écart de performance par rapport au simple hold ne montre aucune amélioration statistiquement vérifiable.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
