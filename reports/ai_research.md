# Seiko Trading Lab — analyse de robustesse et hypothèses IA

Statut : **model_reflection_completed**. Données historiques uniquement. Aucune proposition n'a été validée en simulation prospective.

## Faits mesurés

- BTCUSD : -2.66 % rendement net moyen, 1.02 points face au Hold, -5.32 % avec frais doublés, 11 trades clôturés, drawdown maximal 19.51 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs.
- ETHUSD : 7.49 % rendement net moyen, 4.43 points face au Hold, 5.17 % avec frais doublés, 7 trades clôturés, drawdown maximal 25.17 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, beats_hold_in_most_folds, drawdown_below_20_pct.
- SOLUSD : -4.37 % rendement net moyen, -1.39 points face au Hold, -7.99 % avec frais doublés, 15 trades clôturés, drawdown maximal 35.01 % sur 8 fenêtres ; blocages : twenty_or_more_closed_trades, positive_average_net_return, beats_hold_in_most_folds, positive_average_with_double_costs, drawdown_below_20_pct.

## Pistes d'expériences

- **BTCUSD — Validation prospective du drawdown sous contrainte de frais doubles** : Collecter une nouvelle serie temporelle de donnees de carnet d'ordres et d'execution a haute frequence pour BTCUSD sur un echantillon totalement disjoint, puis simuler un scenario de doublement des frais de transaction. Critère d'abandon : Si le rendement net moyen reste positif et superieur au benchmark de conservation avec des frais doubles sur la nouvelle serie, l'hypothese d'une vulnerabilite systemique aux frais est rejetee.
- **ETHUSD — Verification du drawdown maximal hors echantillon** : Recuperer de nouvelles donnees de profondeur de marche et de transferts publics de stablecoins pour Ethereum sur des periodes passees non encore exploitees, et verifier l'impact sur le pire drawdown de la strategie. Critère d'abandon : Si le pire drawdown observe sur les nouvelles donnees reste strictement inferieur a 20 pourcent sur l'ensemble des fenetres, l'hypothese d'un risque excessif de drawdown est rejetee.
- **SOLUSD — Robustesse du nombre de trades face a de nouvelles donnees de volume** : Integrer de nouvelles donnees de activite de reseau et de volume d'echantillonnage de Solana sur une periode supplementaire non encore testee pour mesurer la frequence reelle des signaux. Critère d'abandon : Si le nombre de trades clotures atteint ou depasse 20 operations avec un ratio de Sharpe ameliore sur ces nouvelles donnees, l'hypothese d'insuffisance statistique liee au faible nombre de trades est rejetee.

Aucun ordre réel, changement de portefeuille ou promotion automatique.
