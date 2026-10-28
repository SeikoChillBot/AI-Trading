# Seiko Trading Lab — expériences multi-actifs, V1
**Mis en place le 28 octobre 2026 — paper trading, aucun ordre réel.**

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
