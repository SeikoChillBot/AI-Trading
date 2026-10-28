# Seiko Trading Lab — laboratoire de trading fictif

**14 robots expérimentaux**, chacun doté de 20 USD fictifs au démarrage. Aucune transaction réelle, aucune clé API privée, aucune garantie de rendement.

**[Ouvrir le tableau de bord](https://seikochillbot.github.io/AI-Trading/)** · [Résultats bruts](reports/latest.csv) · [Historique](reports/history.csv) · [Plan V2](V2_PLAN.md)

## Comprendre les robots

Chaque nom commence par la crypto suivie de sa stratégie : `btc_` = Bitcoin, `eth_` = Ethereum, `sol_` = Solana. Plusieurs robots testent la même stratégie sur des actifs différents pour comparer les résultats.

| Robot | Technique | Quand il achète | Quand il vend |
|---|---|---|---|
| btc_hold | Conservation BTC | Dès qu'il n'a pas de BTC | Ne revend pas |
| eth_hold | Conservation ETH | Dès qu'il n'a pas d'ETH | Ne revend pas |
| sol_hold | Conservation SOL | Dès qu'il n'a pas de SOL | Ne revend pas |
| btc_momentum | Tendance BTC | Prix > moyenne 20 bougies de 0,3 % | Prix < moyenne de 0,3 % |
| eth_momentum | Tendance ETH | Même règle, sur ETH | Même règle, sur ETH |
| sol_momentum | Tendance SOL | Même règle, sur SOL | Même règle, sur SOL |
| btc_reversion | Rebond BTC | Prix 1 % sous moyenne 20 bougies | Prix 0,5 % au-dessus de la moyenne |
| eth_reversion | Rebond ETH | Même règle, sur ETH | Même règle, sur ETH |
| sol_reversion | Rebond SOL | Même règle, sur SOL | Même règle, sur SOL |
| btc_breakout | Cassure BTC | Prix dépasse les 20 clôtures précédentes | Prix sous les 10 clôtures précédentes |
| btc_rsi | RSI BTC | RSI 14 sous 35 (survente) | RSI 14 au-dessus de 60 |
| eth_ema_cross | EMA ETH | EMA 9 > EMA 21 de 0,1 % | EMA 9 < EMA 21 |
| sol_bollinger | Bollinger SOL | Prix sous moyenne 20 moins 2 écarts-types | Prix au-dessus de la moyenne |
| btc_volatility | Cassure volatile BTC | Nouveau sommet 20 bougies et amplitude récente > 1 % | Prix sous moyenne 20 |

### Petit lexique

- **Hold** : acheter et conserver ; sert de point de comparaison.
- **Momentum** : suivre une tendance déjà engagée.
- **Reversion** : chercher un retour vers la moyenne après une baisse.
- **Breakout** : miser sur une cassure au-dessus des prix récents.
- **RSI** : indicateur de force des mouvements récents ; « survente » ne signifie pas rebond garanti.
- **EMA** : moyenne mobile donnant plus de poids aux prix récents.
- **Bollinger** : bandes statistiques autour d'une moyenne.
- **Volatility** : filtre de variation des prix ; plus de mouvement ne signifie pas plus de rentabilité.

## Expérience multi-durées (28 octobre 2026)

Les robots utilisent désormais des bougies clôturées de durées différentes :

| Durée | Robots |
|---|---|
| 5 minutes | btc_momentum, sol_momentum, btc_reversion, sol_reversion, btc_rsi, sol_bollinger |
| 15 minutes | eth_momentum, eth_reversion, btc_breakout, eth_ema_cross |
| 60 minutes | btc_hold, eth_hold, sol_hold, btc_volatility |

Le champ `timeframe_min` dans `reports/latest.csv` indique la durée de chaque robot. Le capital et l'historique antérieurs sont conservés : les rendements cumulés ne permettent donc pas d'attribuer un gain à la nouvelle durée seule. Il faut comparer les évolutions après la date du changement, puis effectuer un backtest indépendant. Les robots Hold servent de références et ne tradent pas plus fréquemment.

## Comment lire les résultats ?

- **Capital** : argent fictif restant + valeur de la crypto détenue.
- **Gain/perte** : différence avec les 20 USD initiaux.
- **Opérations** : achats et ventes ; un achat seul ne représente pas un gain.
- **Meilleur robot** : classement provisoire, pas une preuve de sécurité.
- **Frais** : 0,1 % simulé par achat ou vente, soit environ 0,2 % par aller-retour, avant spread et slippage.

## Fonctionnement et limites

GitHub Actions est programmé pour tenter une exécution toutes les 5 minutes environ (sans garantie de déclenchement ponctuel). Le bot récupère des bougies Kraken BTC/USD, ETH/USD et SOL/USD, et sauvegarde les résultats dans `state/portfolios.json` et `reports/`. Les noms internes `BTCUSDT` etc. sont hérités d'une ancienne version : les prix utilisés sont **USD**, pas USDT ni EUR.

La simulation utilise le prix de clôture de la bougie déclenchant le signal pour simuler son exécution, ce qui est optimiste. Elle ne prend pas en compte le spread, le slippage, la liquidité, les tailles minimales réelles ni la fiscalité. Le classement ne doit pas servir de base à un investissement réel. Les 4 nouveaux robots commencent leur historique lors de leur première exécution ; comparer leur performance depuis le lancement initial de la V1 exige de tenir compte des dates de départ différentes.

## Publication du site

GitHub Pages : **Deploy from a branch → main → /docs**. Le workflow copie le tableau de bord généré dans `docs/index.html`. Après une exécution réussie et le déploiement Pages, rafraîchir le site pour voir les nouveaux résultats.

## Prochaines améliorations

Journal des transactions, suivi du risque et des pertes maximales, backtesting, simulation d'exécution sur la bougie suivante, comparaison hors échantillon et V2 indépendante. Voir [V2_PLAN.md](V2_PLAN.md).
