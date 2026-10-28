# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.66 % rendement net moyen, 1.02 points face au Hold, -5.32 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 7.49 % rendement net moyen, 4.43 points face au Hold, 5.17 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.37 % rendement net moyen, -1.39 points face au Hold, -7.99 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Test de robustesse des fenêtres OOS supplementaires sur BTCUSD** : Recuperer de nouvelles donnees de carnet d'ordres historiques non utilisees sur BTCUSD pour verifier si les 4 sur 8 folds battant le Hold persistent. Critère d'abandon : Si la proportion de folds battant le Hold reste superieure a 50 pour cent sur les nouvelles donnees, l'hypothese d'absence de robustesse est rejetee.
- **ETHUSD — Verification du drawdown maximum sur ETHUSD avec des donnees de ticks** : Analyser de nouvelles donnees de ticks haute frequence non exploitees pour ETHUSD afin de recalculer le pire drawdown. Critère d'abandon : Si le drawdown recupere reste inferieur a 25 pour cent sur la nouvelle echelle de temps, l'hypothese de sous-estimation du risque est rejetee.
- **SOLUSD — Stress test des couts de transaction doubles sur de nouvelles periodes SOLUSD** : Appliquer des frais doubles sur un ensemble de donnees de prix de SOLUSD entierement separe et non utilise dans les tests precedents. Critère d'abandon : Si le rendement net moyen avec frais doubles devient positif ou superieur a -5 pour cent sur les nouvelles donnees, l'hypothese de fragilite extreme aux frais est rejetee.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
