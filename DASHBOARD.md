# Tableau de bord — AI Trading

Actualisé : **28/10/2026 à 19:44 (heure de Paris)** · **18 robots** · **20 USD fictifs chacun**

> Simulation uniquement, aucun argent réel. Les frais de marché sont simplifiés et les résultats ne sont pas des prévisions.

| Robot | Capital | Gain / perte | Évolution | Opérations |
|---|---:|---:|---|---:|
| sol_momentum | 20.06 $ | +0.30 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▃▄▁▁▁▃█ | 1 |
| sol_scalp_microtrend | 20.06 $ | +0.30 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▃▄▁▁▁▃█ | 1 |
| eth_reversion | 20.04 $ | +0.20 % | ▅▅▅▅▅▄▄▄▃▁▁▁▂▃▄▂▃▂▂▁▃▂▂▆▇█▇ | 2 |
| btc_momentum | 20.04 $ | +0.18 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▃▁▁▁▄█ | 1 |
| eth_momentum | 20.03 $ | +0.17 % | ▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▃▁▄▆█ | 1 |
| btc_reversion | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| eth_ema_cross | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| btc_volatility | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄ | 0 |
| btc_scalp_momentum | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| btc_scalp_conservative | 20.00 $ | +0.00 % | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ | 0 |
| sol_reversion | 20.00 $ | -0.00 % | ▇▇▇▆▇▆▅█▃▄▃▂▁▁▃▃▃▄▅▄▂▄▃▃▄▃▂▅▄▃▃▅▇▇▇▇▇▇▇ | 2 |
| btc_breakout | 20.00 $ | -0.01 % | ████████████████████████▂▁▇ | 1 |
| eth_scalp_trailing | 19.98 $ | -0.10 % | ███████████████████████████████████▁ | 1 |
| btc_hold | 19.97 $ | -0.14 % | ▄█▄█▂▁▁▁▄ | 1 |
| btc_rsi | 19.93 $ | -0.34 % | █▇▄▄▄▃▅▁▄▄▃▂▂▃▃▃▄▄▃▁▂▂▂▁▁▁▃▁▂▂▃▄▄▄▄▄▄▄ | 2 |
| eth_hold | 19.91 $ | -0.43 % | ▅█▄█▁▁▁▁▃ | 1 |
| sol_hold | 19.91 $ | -0.45 % | ▅█▄█▁▁▁▂▃ | 1 |
| sol_bollinger | 19.78 $ | -1.10 % | █▇▅▅▄▄▆▂▃▂▂▁▁▃▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂ | 2 |

## Comprendre les résultats

- **Capital** : valeur actuelle du portefeuille fictif, crypto comprise.
- **Gain / perte** : variation depuis les 20 $ initiaux.
- **Évolution** : mini-courbe des 48 derniers relevés (échelle propre à chaque robot).
- **Opérations** : nombre d'achats et de ventes fictifs.

[Historique détaillé](reports/history.csv) · [Positions actuelles](state/portfolios.json)

**Limites :** simulation en USD, frais forfaitaires de 0,1 %, sans spread ni glissement. Les transactions sont exécutées au prix de clôture du signal : biais favorable à corriger.
