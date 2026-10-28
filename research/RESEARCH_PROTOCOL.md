# Seiko Trading Lab — protocole multi-marchés
_Mis à jour le 28 octobre 2026. Recherche et paper trading uniquement._

## Mission

Explorer un large éventail de véhicules d'investissement et d'approches systématiques sans confondre une idée, un backtest et une simulation avec exécution réelle. Les 18 robots crypto de V2 demeurent un univers indépendant. Aucun autre marché n'est indiqué comme actif tant que sa source de cotation, son modèle de frais et son moteur de simulation n'ont pas été vérifiés.

Le catalogue et ses contraintes alimentent la quatrième vue `Explorer` du tableau de bord : `research/market_catalog.json`. Les catégories ne créent aucune position fictive et n'altèrent pas le total initial de 360 USD de l'expérience crypto.

## Échelle de maturité

| Statut | Définition |
| --- | --- |
| Simulation active | Flux de marché opérationnel, moteur forward-only fonctionnel et journal des tentatives rempli |
| Données / courtier à connecter | Investissement automatisable en principe, mais source précise ou règles de simulation non validées |
| En étude | Analyse d'instruments, d'horizons et de frais, sans exécution simulée |
| Recherche à risque élevé | Instrument complexe : investigation documentaire et tests isolés seulement, aucun levier réel |

## Stratégies candidates, sans présumer de leur rendement

1. **Investissement périodique (DCA)** : un montant fixé à des dates prédéfinies. Comparer au marché et à un achat initial ; gérer les frais, les petites sommes et les dividendes.
2. **Buy & Hold** : référence d'achat-conservation par instrument, avec distributions et éventuel risque de change.
3. **Momentum** : moyenne, force relative, filtre de tendance et rotation à fréquence définie.
4. **Retour à la moyenne** : seuils d'écart préalablement définis, arrêt des positions selon un protocole explicite.
5. **Rééquilibrage** : allocations cibles, coûts de rotation et chevauchement des actifs.
6. **Sélection actions** : qualité, valeur, résultats, dividendes ; données publiées uniquement à leur date de disponibilité, pas de connaissance anticipée.
7. **Revenus** : coupons, dividendes nets, distributions immobilières réellement versées ; distinguer rendement distribué et variation du capital.
8. **Hedging** : protections qui réduisent le risque, en comptant les primes, les spreads et les frais.
9. **Arbitrage/market making** : à explorer seulement si les carnets simultanés, l'exécution et les frais sont observables. Les écarts bruts ne sont pas des profits.
10. **Rendements alternatifs** : staking, prêt, crowdlending ; modéliser défaut, garde, risques contractuels, liquidité et immobilisation du capital.

## Conditions pour déclarer une nouvelle simulation crédible

- **Données** : source nommée, marché et devise exacts, timestamp et fuseau, horodatage d'observation, calendrier de marché, licence d'utilisation vérifiée.
- **Ordres** : signal uniquement à partir d'informations déjà disponibles ; achat/vente plus tard au prix exécutable (bid/ask ou volume sur le carnet), latence et frais du courtier correspondant.
- **Limites** : fractionnement éventuel, minimum d'ordre, contrôle du montant et des fonds, gestion des ordres refusés, des périodes sans cotations et des erreurs de flux.
- **Spécificités** : dividendes/splits et retenues pour actions et ETF, frais courants des fonds, coupons/échéances pour obligations, rollover et marge pour futures, financement/swaps pour devises et CFD, frais de change à la date de transaction.
- **Capital** : une allocation distincte par marché et portefeuille ; ne pas additionner un capital investi deux fois. 20 USD n'est **pas** une mise de référence automatiquement réaliste pour tous les instruments.
- **Historique** : journal immuable des signaux et des ordres, erreurs explicites, positions, liquidités, quantités, coût de revient, devises et frais ; n'inventer ni ordre ni point de prix en cas d'indisponibilité.
- **Règle** : conserver les versions précédentes comme témoins ; aucune nouvelle stratégie ne modifie rétroactivement l'ancienne performance.

## Étapes de recherche, indicateurs et prévention des faux positifs

1. **Backtest historique** : inclure toutes les périodes du cycle de marché, effets d'entreprise, frais et produits disparus ; éviter les biais d'anticipation et de survivance.
2. **Validation hors échantillon** : séparer une période de conception d'une période non vue ; évaluer à plusieurs reprises en walk-forward. Limiter les paramètres et enregistrer toutes les variantes essayées.
3. **Simulation prospective** : sur données de marché observées en temps réel ; laisser des stratégies fonctionner sans réoptimisation répétée sur leurs premiers résultats. Plus de 14 jours et 20 allers-retours seront généralement nécessaires, particulièrement pour les stratégies à horizon mensuel.
4. **Comparaison honnête** : pour chaque stratégie, gain/perte net(te), drawdown, volatilité, liquidité, frais, pourcentage de temps investi, nombre de trades, turnover, profit factor, corrélations, profit relatif à un indice *réellement accessible*, marges d'erreur.
5. **Conditions sévères** : hausse des frais, spread multiplié, latence, journées de volatilité anormale, gaps, liquidité dégradée ; les systèmes doivent pouvoir ne rien faire.
6. **Arbitrage de l'objectif** : distinguer croissance du patrimoine et revenu retiré ; calculer besoins de capital à partir de rendements hypothétiques, non de promesses. Prendre en compte fiscalité individuelle et frais avant toute projection réelle.

## Données/plateformes étudiées, non connectées

- **Kraken** : moteur crypto spot V2, carnet d'ordres public et données OHLC. Fonctionnement vérifié dans le projet, mais simulé.
- **Alpaca Paper Trading** : compte *paper-only* accessible selon sa documentation, accès gratuit aux données actions et ETF US de la place IEX uniquement ; ne couvre pas tout le carnet consolidé américain, ni automatiquement les ETF UCITS européens.
- **Interactive Brokers Paper Trading** : simulation multi-instruments et API ; les conditions de compte approuvé/financé et abonnements de données sont distinctes. Non connecté.
- **BCE** : taux de référence EUR/USD pour la conversion d'affichage uniquement, **pas** un prix d'exécution Forex.

## Expositions complexes

Les dérivés, CFD, Forex à levier, crypto lending, DeFi et investissements non cotés sont conservés comme domaines d'étude à haut risque et ne sont pas activés automatiquement. Les produits très risqués ne constituent pas une solution pour garantir un revenu mensuel.

## Références vérifiées

- AMF ETF : https://www.amf-france.org/fr/espace-epargnants/comprendre-les-produits-financiers/placements-collectifs/trackers-etf
- AMF obligations : https://www.amf-france.org/fr/espace-epargnants/comprendre-les-produits-financiers/actions-obligations/obligations/comprendre-les-obligations-avant-dinvestir
- AMF CFD : https://www.amf-france.org/fr/espace-epargnants/comprendre-les-produits-financiers/produits-complexes/cfd
- AMF crowdfunding immobilier : https://www.amf-france.org/fr/espace-epargnants/comprendre-les-produits-financiers/financement-participatif-crowdfunding/investir-le-crowdfunding-immobilier
- Alpaca paper trading : https://docs.alpaca.markets/us/docs/paper-trading
- Alpaca data : https://docs.alpaca.markets/us/docs/about-market-data-api
- Interactive Brokers : https://www.interactivebrokers.eu/campus/glossary-terms/paper-trading-account/
- BCE euro reference : https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
