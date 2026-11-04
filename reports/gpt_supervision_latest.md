# Seiko Lab — supervision indépendante GPT du 4 novembre 2026

Contrôle du 04/11/2026 vers 14h44–14h55 Europe/Paris. **Faits** ci-dessous issus des JSON publiés sur `main` et des journaux GitHub Actions. **Propositions** non exécutées identifiées séparément. Aucun ordre réel ; 20 USD fictifs par robot/scénario.

## Gemini : génération réelle, mais apport structuré toujours insuffisant

- `reports/ai_research_status.json` et `reports/ai_research_proposals.json` : génération à **12:13:03 UTC (13h13 Paris)**, `state=model_reflection_completed`, `provider=gemini`, `source=gemini_generate_content`, `used_cache=false`, `attempts_in_slot=1`. Le run recherche **#41827285554**, terminé avec succès, a exécuté l'étape Gemini et publié ses observations via le commit automatique **dd27475** à **12:13:18 UTC**. C'est une réponse **nouvelle** ; ni cache, ni repli statistique.
- Contenu : **1 expérience narrative** BTC breakout avec frais doublés, **1 ajustement proposé** `btc_momentum entry_scale=1.2`, mais **0 `scenario_proposals`, 0 `strategy_designs`, 0 `research_tasks`**. Aucun changement de robot validé ni exécuté par Gemini. Les **21 scénarios** du registre de placement sont tous `quantitative_auto_fallback` (9 actifs au moment du rapport), **0 initié par Gemini**.
- **Contre-analyse GPT :** le critère de rejet proposé pour les frais doublés (« baisse du net > double de l'augmentation des frais ») est mal discriminant : à transactions identiques, la variation du rendement net découle mécaniquement des frais supplémentaires, et ne démontre pas la persistance du signal. Pour tester la robustesse, il faut comparer à dates et transactions identiques frais normaux/doublés, résultat net absolu et excès sur Hold, puis tester séparément une variante de signal sur observations futures appariées. Le `entry_scale=1.2` est une hypothèse non validée, pas une recommandation d'activation.

## Robots fictifs : résultats vérifiés à 13:37 UTC (14h37 Paris)

- **Crypto, 18 × 20 USD** : **296,31691/360 USD**, rendement net **−17,6897 %**, drawdown maximal agrégé observé **18,0078 %**, **385 ordres exécutés**, **190 allers-retours clôturés**, **51,47017 USD de frais cumulés** (soit 14,30 % des 360 USD initiaux), 0 stratégie qualifiée. Les 15 stratégies crypto non-Hold sont déficitaires ; **1/15 seulement dépasse son Hold** sur l'historique courant : `btc_scalp_conservative` **−1,8205 %** contre `btc_hold` **−4,7833 %**, soit +2,9628 points relatifs mais **pas de bénéfice absolu**. Le taux de qualification exige 14 jours et 20 allers-retours par stratégie ; l'expérience n'a que 6,80 jours environ.
- **Multi-actifs, 18 × 20 USD** : **354,61598/360 USD**, **−1,4956 %**, **0 qualifié**, 1 aller-retour clôturé au total, 0,26871 USD de frais modélisés. Deux stratégies affichent un rendement provisoire positif, sans qualification ; plusieurs cotations sont retardées/indicatives, dividendes/splits non modélisés, conversion FX non exécutable. Ne pas comparer leur risque à la crypto comme s'il s'agissait de marchés et horizons homogènes.
- **Recherche prospective** : 18 pistes suivies pendant **6 journées** chacune, **5 transactions clôturées** au total ; **0/18 rendement net positif**, **16/18 devant Hold**, principalement parce que plusieurs restent à 0 % en liquidités pendant une baisse. Aucune piste avec `sufficient_evidence=true`. Un exemple négatif concret : `SOLUSD mean_reversion` **−14,85507 %** net, **−3,83788 points** contre Hold, drawdown **14,85507 %**, 3 clôtures.
- **Évolution** : 36 robots suivis, **12 témoins Hold immuables**, **24 réglages en test**, **0 adopté**. Exemple `aapl_trend20` : 6,5/30 jours, 0/20 transactions de validation, 3/24 observations futures ; blocages frais doublés et rendement net toujours présents. Les tests historiques ne remplacent pas les données prospectives.

## Données, scénarios et couverture

- `reports/market_knowledge.json` : **7 journées** d'observations synchronisées, insuffisantes pour attribuer une causalité aux signaux de marché. Directeur de recherche : 3 plans locaux BTC/ETH/SOL, **6 journées** chacun, aucun nouveau plan dirigé par Gemini ; Foundry : **18 hypothèses, 0 Gemini**.
- `reports/ai_daily_brief.json` du 04/11 : **1 nouveau scénario** fictif aujourd'hui, issu du repli quantitatif, **0 Gemini**, 0 réglage activé. Le rapport quotidien ne constitue pas une analyse GPT indépendante.
- Suivi des gros transferts : **150 USDC + 150 USDT** échantillonnés, **3 gros transferts** observés, 4 adresses publiques suivies, **0 nouveau transfert** dans le rapport de suivi d'adresses. Couverture partielle ; aucune preuve d'identité, d'achat ou de vente. Le suivi ne pilote pas directement les 36 robots. **Proposition** : comparer en shadow une hypothèse « transfert + confirmation prix/volume » à un témoin sans signal on-chain sur observations futures datées ; ne pas l'intégrer aux robots avant preuve de gain net et contrôle de faux signaux.

## Workflows, modifications et limites

- Recherche **#41827285554** : SUCCESS ; étapes de collecte, recherche, Gemini, directeur, scénarios, validation du site et publication SUCCESS ; journal confirme `main -> main` et commit **dd27475** à 12:13:18 UTC.
- Simulation **#41839781339** à 13:37 UTC : SUCCESS ; tests de sécurité, moteurs crypto/multi-actifs, interface et publication des portefeuilles SUCCESS. Le rapport de simulation plus récent est bien présent dans `reports/`. Pages **#41839831336** SUCCESS.
- **Aucun correctif de code effectué** lors de cette supervision : pas de panne ciblée de Gemini ou de publication démontrée. Aucune modification de robots, de leurs historiques, des Hold, de l'interface, des clés ou des règles de risque. Les tests ont été exécutés par les workflows consultés ; **aucun test local supplémentaire** ni test d'une nouvelle stratégie n'a été effectué.
- **Limites d'accès** : les secrets et facturations du fournisseur ne sont pas inspectés ; les traces prouvent une réponse Gemini et une publication, **pas l'absence de toute facturation externe**. Les prix de marché, transferts et flux sont des échantillons, pas des confirmations de transactions réelles. Les performances ne sont pas une prévision.

## Travaux incomplets et prochaine action

1. Accumuler au moins les journées et transactions prospectives requises ; ne promouvoir aucune variante avant les garde-fous de frais normaux/doublés, net absolu, excès sur Hold et drawdown.
2. Examiner un **protocole expérimental shadow** pour le signal de gros transferts, avec appariement temporel, contrôle sans transfert, sources et qualité de couverture ; **non implémenté**.
3. Débloquer conceptuellement le directeur saturé par trois plans locaux (voie shadow parallèle bornée, **non implémentée**) sans réinitialiser les plans actifs.
4. Demander à Gemini des propositions structurées falsifiables ; l'appel récent ne démontre pas encore cette capacité. Ne pas multiplier les appels payants ni inventer des résultats.

**Conclusion GPT :** Gemini a réellement répondu et publié aujourd'hui, mais n'a pas fourni de stratégie structurée exécutable. Les simulations continuent de perdre après frais ; aucune rentabilité robuste n'est prouvée. Le prochain progrès mesurable est une recherche prospective mieux contrôlée, non une modification immédiate des 36 robots.
