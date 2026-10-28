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

## Comparaison demandée : 10 techniques distinctes

Chaque robot V2 partira de 20 USD fictifs et aura une technique principale différente ; les paramètres seront gelés avant la comparaison en conditions identiques.

| Robot | Technique candidate | Hypothèse testée |
|---|---|---|
| V2-01 | EMA 9/21 avec filtre de tendance | Capturer les impulsions courtes |
| V2-02 | RSI de retour à la moyenne | Acheter un repli temporaire |
| V2-03 | Bandes de Bollinger | Profiter du retour vers la moyenne |
| V2-04 | Cassure du canal de Donchian | Suivre une sortie de range |
| V2-05 | MACD avec filtre de volatilité | Filtrer les faux signaux de momentum |
| V2-06 | VWAP avec confirmation du volume | Exploiter les écarts au prix moyen pondéré |
| V2-07 | Stochastique en marché latéral | Rechercher les oscillations de range |
| V2-08 | ATR et breakout de volatilité | Éviter les mouvements trop faibles |
| V2-09 | Momentum multi-horizon | Confirmer la direction sur deux horizons |
| V2-10 | Régime de marché + sélection de signal | Adapter l'entrée à la tendance ou au range |

**Attention :** ce sont des hypothèses expérimentales, pas des techniques dont la rentabilité est démontrée. Pour isoler l'effet de la technique, tester autant que possible les mêmes actifs et périodes, et documenter les différences d'exposition.

### Objectif de gain
L'utilisateur vise 1 à 2 EUR nets par transaction. Sur un capital de 20 USD, cela implique un ordre de grandeur de 5 à 10 % du capital initial par trade, sans compter les conversions de devises ; ce n'est **pas** un objectif réaliste pour du scalping prudent à faible risque. Ne pas forcer les trades pour atteindre cette cible. Évaluer plutôt l'espérance nette par transaction, la distribution des gains/pertes, la fréquence et le drawdown.

### Statut
Ce document définit les stratégies à développer. Aucun robot V2 n'est encore activé et la V1 n'a pas été modifiée.
