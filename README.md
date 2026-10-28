# AI-Trading — laboratoire de simulation

**Simulation uniquement : aucun ordre réel, aucune clé d'exchange, aucun dépôt.**

Dix portefeuilles indépendants de **20 USDT fictifs chacun** sont évalués sur les cours publics BTC, ETH et SOL, environ toutes les 15 minutes via GitHub Actions. L'objectif initial était 20 €, mais les cotations de cette version sont en USDT : **les résultats ne sont pas des euros**.

## Démarrage
Ouvrir **Actions → Paper trading → Run workflow** pour le premier test. Le workflow conserve son état dans `state/portfolios.json` et écrit le classement dans `reports/latest.csv`. Les exécutions planifiées peuvent être retardées ou ignorées.

## Stratégies
3 achats-conservation, 3 momentum, 3 retours à la moyenne, 1 breakout. Ce sont des algorithmes explicites, **pas des IA**.

## Limites
- Les cours sont en USDT ; il n'y a pas de conversion EUR/USDT.
- Frais simulés de 0,1 % par transaction, sans spread, glissement, fiscalité ni frais de change. Résultats potentiellement optimistes.
- Les ordres sont fictifs et calculés au prix de clôture de la bougie ayant servi au signal : cela crée un **biais d'exécution favorable**. Corriger avant toute comparaison sérieuse.
- Un seul ordre par bougie clôturée, état sauvegardé dans GitHub.
- L'API Binance peut être inaccessible depuis certains environnements. Le job échouera sans passer d'ordre.
- GitHub Actions utilise des quotas et exige l'autorisation d'écriture pour sauvegarder les résultats.
- Sept jours ne suffisent pas à démontrer la rentabilité.

## Suite
Corriger la simulation pour exécuter les signaux sur la bougie suivante, ajouter une conversion EUR réelle, le journal des transactions, le suivi de l'équité et une comparaison hors échantillon. Ne pas connecter de fonds réels à ce prototype.
