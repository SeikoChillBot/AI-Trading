# Tableau de bord — AI Trading

Actualisé : **28/10/2026 à 13:24 (heure de Paris)** · **14 robots** · **20 USD fictifs chacun**

> Simulation uniquement, aucun argent réel. Les frais de marché sont simplifiés et les résultats ne sont pas des prévisions.

| Robot | Capital | Gain / perte | Évolution | Opérations |
|---|---:|---:|---|---:|
| btc_momentum | 20.00 $ | +0.00 % | ▄▄▄ | 0 |
| eth_momentum | 20.00 $ | +0.00 % | ▄▄▄ | 0 |
| sol_momentum | 20.00 $ | +0.00 % | ▄▄▄ | 0 |
| btc_reversion | 20.00 $ | +0.00 % | ▄▄▄ | 0 |
| eth_reversion | 20.00 $ | +0.00 % | ▄▄▄ | 0 |
| sol_reversion | 20.00 $ | +0.00 % | ▄▄▄ | 0 |
| btc_breakout | 20.00 $ | +0.00 % | ▄▄▄ | 0 |
| eth_ema_cross | 20.00 $ | +0.00 % | ▄▄ | 0 |
| btc_volatility | 20.00 $ | +0.00 % | ▄▄ | 0 |
| btc_hold | 19.98 $ | -0.09 % | ▁█▁ | 1 |
| btc_rsi | 19.98 $ | -0.10 % | █▁ | 1 |
| sol_bollinger | 19.98 $ | -0.10 % | █▁ | 1 |
| sol_hold | 19.96 $ | -0.22 % | ▂█▁ | 1 |
| eth_hold | 19.92 $ | -0.38 % | ▃█▁ | 1 |

## Comprendre les résultats

- **Capital** : valeur actuelle du portefeuille fictif, crypto comprise.
- **Gain / perte** : variation depuis les 20 $ initiaux.
- **Évolution** : mini-courbe des 48 derniers relevés (échelle propre à chaque robot).
- **Opérations** : nombre d'achats et de ventes fictifs.

[Historique détaillé](reports/history.csv) · [Positions actuelles](state/portfolios.json)

**Limites :** simulation en USD, frais forfaitaires de 0,1 %, sans spread ni glissement. Les transactions sont exécutées au prix de clôture du signal : biais favorable à corriger.
