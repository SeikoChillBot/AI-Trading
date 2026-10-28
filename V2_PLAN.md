# AI-Trading V2 — Micro-trading expérimental

Statut : cahier des charges, non déployé. La V1 reste inchangée.

## Objectif
Tester des stratégies qui recherchent de nombreux petits gains **nets** sans forcer les transactions. Aucune garantie de rentabilité.

## Architecture
- 10 portefeuilles V1 inchangés comme groupe témoin.
- V2 dans un module et un état séparés (ex. `v2/`, `state/v2_portfolios.json`, `reports/v2_*.csv`).
- Paper trading exclusivement : aucune clé privée, aucun ordre réel.
- BTC/USD, ETH/USD et SOL/USD sur Kraken ; ne pas confondre les libellés USDT hérités de la V1 avec des cotations USD.
- Bougies terminées uniquement ; signal sur la bougie clôturée, exécution simulée au prix suivant disponible, jamais au cours qui a servi à produire le signal.

## Stratégies candidates
1. Momentum court terme avec filtre de tendance et de volatilité.
2. Retour à la moyenne avec RSI et bandes de Bollinger, en régime non tendanciel.
3. Cassure avec confirmation du volume et filtre anti-faux signaux.
4. Scalping prudent sur impulsion, sous réserve d'une granularité de données et de coûts suffisante.

## Garde-fous
- Comptabiliser frais à l'entrée et à la sortie, spread, slippage et éventuelles tailles minimales d'ordre.
- Ne pas entrer si le rendement attendu net des coûts ne dépasse pas une marge de sécurité calibrée hors échantillon.
- Taille de position plafonnée, stop-loss, limite de perte journalière, période de refroidissement après pertes.
- Refuser le trade si les données sont anciennes, manquantes ou incohérentes.
- Ne pas promettre un gain sur chaque transaction ; aucune stratégie ne peut le garantir.

## Validation avant déploiement
1. Construire des tests unitaires et vérifier la comptabilité des transactions.
2. Backtest avec coûts réalistes, sans fuite d'information, séparation entraînement/validation/test et analyse walk-forward.
3. Comparer avec buy-and-hold et V1 sur les mêmes périodes.
4. Mesurer P&L net, win rate, profit factor, drawdown max, nombre de trades, turnover et stabilité selon les régimes.
5. Déployer seulement après validation, avec état indépendant et tableau de bord comparatif.

## Note de faisabilité
Avec 20 USD par portefeuille et 0,1 % de frais par côté, l'aller-retour coûte environ 0,2 % hors spread/slippage. Un grand nombre de petits trades peut être perdant malgré un taux de réussite élevé. Les données OHLC 15 minutes de la V1 ne suffisent pas à simuler fidèlement du scalping intrabougie.
