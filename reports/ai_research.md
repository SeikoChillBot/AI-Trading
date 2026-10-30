# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -1.56 % rendement net moyen, 2.80 points face au Hold, -3.86 % avec frais doublés, 9 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, positive_average_with_double_costs.
- ETHUSD : 7.40 % rendement net moyen, 5.40 points face au Hold, 5.08 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.92 % rendement net moyen, -0.03 points face au Hold, -8.91 % avec frais doublés, 16 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de résistance à la volatilité et frais doublés sur BTC** : Exécuter une simulation de placement fictif de 20 USD en position longue spot sans levier sur BTCUSD pendant 3 jours, en évaluant l'impact de frais de transaction doublés par rapport au témoin Hold. Critère d'abandon : Rejeter l'hypothèse si le rendement net après frais doublés est inférieur ou égal au rendement du témoin Hold sur la même période de 3 jours.
- **ETHUSD — Validation de tendance sur ETH face aux mouvements de marché** : Lancer une simulation prospective de placement fictif de 20 USD en spot long sans levier sur ETHUSD pendant 7 jours en conditions de marché baissier échantillonné. Critère d'abandon : Rejeter l'hypothèse si le drawdown maximum dépasse 10 % ou si le rendement excédentaire par rapport au Hold reste négatif à l'issue des 7 jours.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
