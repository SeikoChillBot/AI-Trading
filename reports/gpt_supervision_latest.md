# Seiko Lab — supervision indépendante GPT du 6 novembre 2026

**Contrôle :** 06/11/2026 vers 14h34 Europe/Paris. Sources : branche `main` du dépôt `SeikoChillBot/AI-Trading`, rapports JSON datés, workflow de recherche [42217932470](https://github.com/SeikoChillBot/AI-Trading/actions/runs/42217932470), simulation [42226416806](https://github.com/SeikoChillBot/AI-Trading/actions/runs/42226416806). Aucun ordre réel, aucun accès courtier, 20 USD fictifs par robot/scénario. Ce document est une contre-analyse GPT, pas une sortie Gemini.

## Gemini : génération nouvelle confirmée, recherche structurée toujours absente

- `reports/ai_research_status.json` et `reports/ai_research_proposals.json` datés **12:29:05 UTC (13h29 Paris)** : `state=model_reflection_completed`, `provider=gemini`, `source=gemini_generate_content`, `used_cache=false`, `model_last_called_at=2026-11-06T12:29:05Z`. Les journaux du workflow de recherche 42217932470 indiquent `Read-only AI research: model_reflection_completed`, étape réussie, puis publication réussie. **Nouvelle réponse Gemini réelle**, et non cache ou repli statistique.
- Deux expériences **narratives non exécutées** : BTC breakout avec frais doublés, ETH filtre de faible volatilité sur trois jours ; trois suggestions de seuil (`btc_momentum` 1,2 ; `eth_momentum` 0,8 ; `sol_momentum` 1,2). **Zéro** `scenario_proposals`, `strategy_designs`, `research_tasks`, `experiments_validated=false`. Les suggestions ne sont pas des réglages activés.
- `reports/ai_placement_experiments.json` : **30 essais** enregistrés, **30 `quantitative_auto_fallback`**, 0 Gemini ; 27 `market_selloff`, 3 `market_uptrend`, 0 `sampled_large_transfer`. Le nom du module ne doit pas être interprété comme une attribution à Gemini.
- Le journal quotidien `reports/ai_daily_brief.json` (12:29 UTC) enregistre le bilan du 6 novembre `in_progress`, 3 nouveaux essais statistiques et 0 Gemini ; il ne prouve aucune performance future.

## Résultats des robots fictifs — dernières mesures 13:33 UTC (14h33 Paris)

| Indicateur | Crypto (18 robots) | Multi-actifs (18 robots) |
| --- | ---: | ---: |
| Capital initial fictif | 360 USD | 360 USD |
| Capital actuel fictif | **280,76824 USD** | **355,99298 USD** |
| Rendement net publié | **−22,0088 %** | **−1,1131 %** |
| Frais simulés cumulés (somme par robot) | **63,57710 USD** | **0,33757 USD** |
| Allers-retours clôturés | **245** | **1** |
| Robots qualifiés | **0/18** | **0/18** |

- Crypto : 496 ordres exécutés, drawdown maximal agrégé observé **22,0786 %**. **0/15 stratégies non-Hold** bénéficiaires ; **1/15** devant son Hold, mais toujours négative. Les plus faibles : `sol_scalp_microtrend` −52,1648 %, `sol_bollinger` −50,2657 %, `btc_rsi` −49,5926 %.
- La somme des frais crypto représente **17,66 % du capital initial**, mais **ne doit pas être simplement soustraite à nouveau** du rendement net déjà publié. Les pertes ne peuvent pas être imputées exclusivement aux frais sans rejouer les mêmes signaux et périodes avec coûts alternatifs.
- Multi-actifs : cotations `DELAYED_OR_CLOSED` ou `REFERENCE_ONLY`, données non directement exécutables ; dividendes/splits et autres coûts non intégralement modélisés. Le résultat proche de zéro n'est pas une preuve de profit investissable.
- Différence depuis le dernier rapport GPT du 5 novembre : crypto 293,67 USD environ → 280,77 USD, soit une nouvelle dégradation d'environ **12,90 USD fictifs**. Comparaison de deux instantanés, pas un P&L réalisé.

## Recherche indépendante GPT — critique des hypothèses

- `reports/strategy_forward.json` : **24 pistes actives**, 6 archivées ; 12 à **8 jours** et 12 à **1 jour** d'observations ; seulement **5 clôtures** au total, **0 candidat qualifié** et **0 rendement net positif**. **23/24** dépassent Hold, mais la plupart par maintien en liquidités pendant la baisse. Il serait trompeur d'appeler ces résultats des stratégies gagnantes.
- `reports/research_director.json` : 3 plans locaux BTC/ETH/SOL à **8 jours prospectifs**, aucun plan Gemini initié ce cycle ; les contraintes historiques de 90 jours et 10 trades pour le directeur ne sont pas satisfaites. `reports/strategy_foundry.json` : **30 hypothèses**, 0 attribuée à Gemini.
- `reports/market_knowledge.json` : **9 journées** de marché synchronisées, dernier jour crypto clôturé le 5 novembre ; données trop courtes pour prouver un effet prédictif. BTC −5,546 %, ETH −7,765 %, SOL −6,605 % sur une journée selon l'instantané ; ce contexte baissier peut expliquer un avantage apparent du cash contre Hold.
- **BTC, frais doublés :** une baisse du rendement net à transactions identiques serait attendue arithmétiquement ; il faut tester **le signal lui-même** contre Hold et un contrôle sans filtre, sur mêmes périodes, mêmes coûts, et éviter de confondre changement des frais et changement de sélectivité.
- **ETH, filtre calme :** proposition non exécutée ; comparer à ETH Hold et à la stratégie sans filtre, avec frais normaux/doublés, drawdown, exposition, nombre de trades et observations futures. Une absence de transactions n'est ni un succès ni un échec économique démontré.
- **Suggestions momentum Gemini :** ne pas activer les seuils 1,2 / 0,8 / 1,2 sans validation prospective indépendante, coûts et risque. `reports/robot_evolution.json` : 36 suivis, 12 Hold immuables, 24 variantes en test, **0 activée**.

## Baleines : surveillance effective, aucun avantage démontré

- `reports/large_transfer_observations.json` à 12:28:53 UTC : 150 transferts USDC + 150 USDT échantillonnés, 150+150 validés, **0 transfert ≥1 M USD dans cet échantillon** ; échantillon **non exhaustif**, donc ce n'est pas « aucune baleine sur Ethereum ».
- `reports/whale_follow.json` à 12:28:58 UTC : 4 adresses pseudonymes suivies, 4 nouveaux transferts enregistrés ; aucune identité ni intention d'achat/vente vérifiée. Les événements du suivi d'adresses ne sont pas équivalents aux « gros transferts » détectés dans le nouvel échantillon.
- **0 des 30 scénarios** enregistrés déclenché par `sampled_large_transfer`. **Proposition non implémentée :** comparer prospectivement, en shadow paper, une règle filtrée par transferts et une règle témoin non filtrée, sur les mêmes observations et coûts, sans changer les 36 robots. En l'absence de signal nouveau, ne pas forcer un essai fictif.

## Workflows, corrections, limites et prochaine action

- Workflow de recherche **42217932470**, 12:28–12:29 UTC : **SUCCESS** ; étapes Gemini, validations, tests ciblés et publication toutes **success**. Journaux relus, notamment tests de recherche, historique, on-chain et interface mobile. Le journal prouve une exécution réussie, pas une stratégie rentable.
- Workflow Paper trading **42226416806**, 13:33 UTC : **SUCCESS** ; rapports actualisés à 13:33 UTC. Déploiement Pages de 13:33 UTC **encore en cours au moment de la consultation** ; déploiement précédent **42225131918 SUCCESS**.
- **Aucun correctif de code appliqué** : pas d'anomalie technique bloquante démontrée aujourd'hui. **Seule modification persistée : ce rapport indépendant**. Aucun changement de stratégie, paramètre, historique, Hold, interface mobile, workflow, secret ou facturation.
- **Limites explicites :** aucun test local exécuté par GPT, aucun contrôle de rendu Android physique, aucun accès à la facturation Gemini ; les tests CI du workflow ne remplacent pas une validation économique indépendante.
- **Prochaine action :** accumuler des journées et transactions futures, vérifier la persistance des appels Gemini sans cache, puis concevoir une voie `shadow` supplémentaire pour expériences structurées et transferts, avec comparaisons appariées et critères de rejet explicites. Ne pas modifier les robots avant validation.
