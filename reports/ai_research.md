# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -3.76 % rendement net moyen, 1.22 points face au Hold, -6.67 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 4.97 % rendement net moyen, 5.36 points face au Hold, 2.30 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -5.18 % rendement net moyen, -0.31 points face au Hold, -9.40 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance aux frais accrus sur Bitcoin** : Rejouer les ordres avec les frais normaux puis majorés de 100% sur les prochaines données indépendantes de paper trading. Critère d'abandon : Si le rendement net reste supérieur ou égal au cas de base après doublement des frais, l'hypothèse de sensibilité est réfutée.
- **ETHUSD — Comparaison de filtrage de volatilité sur Ethereum** : Suivre en portefeuille fictif séparé une variante eth_reversion avec filtre actif sur 3 jours, comparée au hold de référence. Critère d'abandon : Si la variante surperforme systématiquement le hold sans augmentation disproportionnée du drawdown, l'hypothèse est réfutée.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
