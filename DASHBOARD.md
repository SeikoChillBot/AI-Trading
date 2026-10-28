# Tableau de bord — AI Trading

Actualisé : **28/10/2026 à 17:16 (heure de Paris)** · **18 robots** · **20 USD fictifs chacun**

> Simulation uniquement, aucun argent réel. Les frais de marché sont simplifiés et les résultats ne sont pas des prévisions.

| Robot | Capital | Gain / perte | Évolution | Opérations |
|---|---:|---:|---|---:|
| btc_momentum | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| eth_momentum | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| sol_momentum | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| btc_reversion | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| btc_breakout | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| eth_ema_cross | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| btc_volatility | 20.00 $ | +0.00 % | ▄▄▄▄▄▄ | 0 |
| btc_scalp_momentum | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| eth_scalp_trailing | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| sol_scalp_microtrend | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| btc_scalp_conservative | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| eth_reversion | 19.93 $ | -0.34 % | █████▆▅▆▄▁▁▁▂▅▆▃▃▃ | 1 |
| btc_rsi | 19.89 $ | -0.54 % | █▇▄▄▄▃▅▁▄▄▃▂▂▃▃▃▄▄▃▁▂▂ | 1 |
| sol_reversion | 19.89 $ | -0.54 % | ▇▇▇▆▇▆▅█▃▄▃▂▁▁▃▃▃▄▅▄▂▄▃ | 1 |
| btc_hold | 19.89 $ | -0.57 % | ▄█▄█▂▁▁ | 1 |
| eth_hold | 19.83 $ | -0.87 % | ▅█▄█▁▁▁ | 1 |
| sol_hold | 19.78 $ | -1.08 % | ▅█▄█▁▁▁ | 1 |
| sol_bollinger | 19.78 $ | -1.10 % | █▇▅▅▄▄▆▂▃▂▂▁▁▃▂▂▂▂▂▂▂▂ | 2 |

## Comprendre les résultats

- **Capital** : valeur actuelle du portefeuille fictif, crypto comprise.
- **Gain / perte** : variation depuis les 20 $ initiaux.
- **Évolution** : mini-courbe des 48 derniers relevés (échelle propre à chaque robot).
- **Opérations** : nombre d'achats et de ventes fictifs.

[Historique détaillé](reports/history.csv) · [Positions actuelles](state/portfolios.json)

**Limites :** simulation en USD, frais forfaitaires de 0,1 %, sans spread ni glissement. Les transactions sont exécutées au prix de clôture du signal : biais favorable à corriger.
