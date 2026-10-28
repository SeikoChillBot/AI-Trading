# Seiko Trading Lab — expériences multi-actifs, V1
**Mis en place le 28 octobre 2026 — paper trading, aucun ordre réel.**

## Expérience actuelle : micro-investissement V2 (20 $ fictifs par robot)

L'utilisateur a indiqué qu'il ne pourrait pas engager 1 000 $ par robot. La simulation doit partir de **20 USD fictifs par stratégie**, et aucun capital réellement disponible n'est présumé.

- **18 robots indépendants × 20 USD = 360 USD de capital de test théorique.** Avec les 18 robots crypto existants, cela représente 36 scénarios indépendants × 20 USD. Il ne s'agit en aucun cas de sommes à déposer simultanément.
- **Nouveau départ enregistré : 28 octobre 2026 à 20:47:23 UTC (21:47, Paris).** La cohorte précédente à 1 000 USD reste intacte dans les anciens fichiers. Aucune donnée historique ancienne n'est convertie ou fusionnée.
- Moteur `multi_asset_sim.py` : `START=20.0`, `schema=2`. Journaux actifs séparés : `state/multi_asset_micro_portfolios.json`, `reports/multi_asset_micro_latest.csv`, `reports/multi_asset_micro_history.csv`, `reports/multi_asset_micro_orders.csv`, `reports/multi_asset_micro_sources.json` et `reports/multi_asset_micro_metrics.json`.
- **Scénario de fractions d'actions** : quantités à six décimales pour la recherche, minimum d'entrée de 1 USD, commission hypothétique de 0,1 % sans frais fixes minimum, demi-spread et slippage simulés. **Les fractions ne sont pas validées titre par titre auprès d'un courtier : ces transactions sont marquées `SIMULATED_FILL_FRACTIONAL_UNVERIFIED`.** Ne jamais appeler ce scénario une exécution réelle ou garantie.
- Certains courtiers prennent en charge des actions fractionnées, mais doivent vérifier `fractionable`, les règles de compte, l'accès depuis la France, les ETF accessibles à un particulier de l'EEE et les frais. Sources : https://alpaca.markets/support/fractional-shares ; https://alpaca.markets/support/how-do-i-know-if-an-asset-is-fractionable ; https://www.interactivebrokers.eu/campus/trading-lessons/fractional-shares/
- Les taux de la BCE restent purement informatifs et non négociables ; les données Yahoo publiques restent non officielles et potentiellement différées. Dividendes, fiscalité et actions sur titres non intégrés.
- Le tableau de bord LAB/04 lit uniquement la cohorte `micro`. La cohorte à 1 000 USD doit rester archivée, sans être présentée comme le budget envisagé par l'utilisateur.
- Premier cycle V2 vérifié : 9 sources présentes, 18 robots créés, 12 tests automatiques passés. À cette heure les marchés US étaient fermés, donc les entrées actions attendaient ; la référence EUR/USD a servi à une simulation indicative. Toute performance est provisoire.

## Archive historique : expérience V1 à 1 000 USD par robot


## Ce qui est automatisé

Le script `multi_asset_sim.py` suit neuf instruments de référence et deux stratégies chacun, soit **18 robots indépendants** :

| Catégorie | Instruments proxy cotés ou référence | Stratégies |
| --- | --- | --- |
| Actions US | AAPL, MSFT | conservation, tendance SMA20 |
| ETF d'indices US | SPY, QQQ | conservation, tendance SMA20 |
| Obligations via ETF US | BND | conservation, tendance SMA20 |
| Or via ETF US | GLD | conservation, tendance SMA20 |
| Argent via ETF US | SLV | conservation, tendance SMA20 |
| Immobilier coté via ETF US | VNQ | conservation, tendance SMA20 |
| Devises informatives | EUR/USD (BCE) | conservation de devises simulée, tendance SMA20 |

Les ETF US sont ici des **proxies de recherche** et ne sont pas automatiquement achetables par un particulier dans l'EEE. L'or et l'argent ne sont pas des métaux livrables : ce sont des titres cotés qui suivent ces marchés.

**Capital :** 1 000 dollars fictifs par robot, soit 18 000 dollars de référence pour cette nouvelle expérience. Ne pas les additionner à l'expérience crypto de 360 $ ; les deux suivis sont indépendants et doivent être comparés en **pourcentages et risque**, pas par les gains bruts.

**Date de départ réelle :** inscrite automatiquement dans `state/multi_asset_portfolios.json` lors du premier cycle avec au moins une cotation validée. Si aucun fournisseur n'est disponible, aucun état de portefeuille n'est créé.

## Cotations

**Actions et ETF :** récupération prudente du flux public `query1/2.finance.yahoo.com/v8/finance/chart` (source non officielle, avec retard, limitation possible et droits de réutilisation non établis). Les prix et volumes ne couvrent pas de carnet bid/ask, et la source est différente d'un flux d'exécution de courtier.

**EUR/USD :** séries quotidiennes officielles de la Banque centrale européenne via l'API ECB Data Portal. Ces taux sont *expressément destinés à l'information*, **pas à passer des ordres**. La simulation Forex est donc indicative et ne peut pas être considérée comme un compte Forex réel.

Si la réponse API est invalide, bloquée, ancienne ou indisponible, **aucun ordre n'est simulé sur cette source**. L'ancienne valeur peut être retenue pour valoriser une position, avec un indicateur de donnée périmée, jamais comme cotation fraîche.

Les sources externes sont vérifiées toutes les 40 minutes au plus pendant les cycles du simulateur pour limiter les appels, et une cotation déjà mise en cache est revalidée à chaque cycle. L'exécution US n'est envisagée que pendant une fenêtre régulière de marché (09:40–15:55 à New York), et seulement si le dernier prix observé est daté de moins de 35 minutes.

## Règles des robots

- **Conservation :** première entrée si cotation valide en séance puis aucune revente systématique.
- **Tendance 20 séances :** signal d'achat si la dernière clôture **déjà terminée** dépasse sa SMA20 de plus de 0,5 %. Vente quand elle passe plus de 0,5 % dessous. L'ordre hypothétique ne s'exécute que lors de la collecte d'une cotation observée après la séance ayant généré le signal.
- Pas de levier, pas de vente à découvert. Titres US en **parts entières** ; EUR/USD en centièmes d'euro indicatifs.
- Frais **hypothétiques** pour actions/ETF US : 0,1 % avec minimum 1 $ par ordre, plus demi-spread estimé de 0,05 % et glissement supplémentaire de 0,10 % dans chaque sens. Ce **n'est pas le barème contractuel d'un courtier**.
- Forex BCE indicatif : frais simulés 0,15 % + 0,10 % de demi-spread estimé et 0,10 % de glissement par opération ; ces coûts ne sont pas des cotations exécutable réelles.
- Valorisation prudente : valeur liquide estimée au prix observé moins les coûts de sortie simulés.
- Les frais courants des ETF sont normalement incorporés dans leurs cours, mais **dividendes, distributions, splits éventuels, retenues à la source et fiscalité ne sont pas encore intégrés**. Ne pas interpréter les résultats comme une performance totale complète.

## Contrôles et fichiers

- Simulation : `multi_asset_sim.py`.
- Tests hors ligne : `tests/test_multi_asset_sim.py` (refus de petites quantités, frais, signaux, données manquantes, cours périmés, blocage hors séance).
- État : `state/multi_asset_portfolios.json`.
- Dernier relevé : `reports/multi_asset_latest.csv`.
- Historique : `reports/multi_asset_history.csv`.
- Journal des opérations acceptées/refusées : `reports/multi_asset_orders.csv`.
- Provenance/erreurs des données : `reports/multi_asset_sources.json`.
- Cache de quotes : `reports/multi_asset_quotes_cache.json`.
- Tableau de bord GitHub Pages : l'onglet `Explorer` affiche les robots, le capital et le journal **uniquement lorsque 18 lignes de portefeuilles sont publiées**. Sinon, un message d'attente est affiché.
- Workflow GitHub : `.github/workflows/simulate.yml` ; le bloc multi-actifs n'empêche jamais le moteur crypto de continuer.

## Condition pour considérer ce projet opérationnel

**Ne pas confondre “le code est installé” et “des ordres ont été réellement simulés sur des cotations acceptées”.** Vérifier la présence de `reports/multi_asset_latest.csv`, les nombres `feed_count` / `feed_errors` dans `reports/multi_asset_sources.json` et la valeur `new_events`. Si les fournisseurs bloquent le runner, l'interface doit rester en attente ; le prochain choix est un flux d'API officiel avec compte paper-only (par exemple Alpaca) nécessitant une action explicite du propriétaire.

La fiabilité des hypothèses demande un courtier concret, des coûts de marché vérifiables, des données adaptées aux ETF UCITS européens et la prise en compte des dividendes/splits, avant d'envisager de l'argent réel.

## Références
- Yahoo Finance Chart (endpoint public non documenté, à utiliser uniquement avec réserve) : https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=3mo
- ECB API : https://data.ecb.europa.eu/help/api/data
- ECB sur la nature purement informative des taux de référence : https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
- Alpaca paper trading : https://docs.alpaca.markets/us/docs/paper-trading
