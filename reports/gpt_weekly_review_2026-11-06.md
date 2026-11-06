# Seiko Lab — premier bilan de période, 29 octobre → 6 novembre 2026

**Auteur :** GPT, synthèse indépendante des rapports publiés ; **pas une réponse de Gemini**.  
**Vérification des dernières données :** 6 novembre 2026, vers 17h23 (Europe/Paris), fichiers de la branche `main`.  
**Nature :** toutes les sommes et opérations évoquées sont fictives et servent à la recherche. Pas d'ordre réel.  
**Portée :** neuf dates de bilans quotidiens (29/10 au 06/11), environ neuf jours de vie pour les portefeuilles créés le 28/10. Il s'agit du premier bilan de période archivé, **pas d'une comparaison statistiquement significative de stratégies**.

## 1. Rendements des deux cohortes, séparément

| Cohorte de 18 robots | Mise initiale fictive | Dernière valeur | Rendement cumulé depuis la création | Maturité |
|---|---:|---:|---:|---|
| Crypto | 360 USD | **279,14941 USD** | **−22,4585 %** | 8,9126 jours, 0 robot évaluable |
| Multi-actifs | 360 USD | **355,95203 USD** | **−1,1244 %** | 8,8168 jours, 0 robot évaluable |

Sources : `reports/realistic_metrics.json` (mis à jour à 16:23:36 UTC) et `reports/multi_asset_micro_metrics.json` (16:23:37 UTC). Ces deux cohortes ont des marchés et modèles distincts : **ne pas fusionner leurs historiques** ni conclure que l'une est supérieure sans tests appariés et qualité de données comparable.

**Crypto :** 507 ordres fictifs remplis, **64,77546 USD** de frais modélisés cumulés dans les fiches des 18 robots, drawdown maximal agrégé observé **22,5466 %**, aucune stratégie actuellement positive (0/18 au dernier contrôle). Le montant de frais ne permet pas à lui seul d'attribuer toute la baisse aux frais : changements de cours et règles de signal interviennent aussi.

**Point de comparaison à sept jours :** le rapport GPT du 30/10 enregistrait **330,73541 USD** pour la cohorte crypto (−8,1291 % depuis sa création). Le 06/11 : **279,14941 USD** (−22,4585 %), soit **−51,586 USD** de valeur fictive entre ces deux relevés, sur des observations prises à des horaires différents. Il s'agit d'une évolution observée, pas d'une expérience causalement contrôlée.

**Multi-actifs :** cotations souvent retardées ou indicatives, effets de dividendes et spécificités de marché non totalement modélisés. 0 robot qualifié. Le faible recul ne permet aucune généralisation.

## 2. Recherche et « apprentissage » réellement observés

- `reports/ai_daily_brief.json`, généré à 15:58:02 UTC le 06/11, conserve **neuf bilans quotidiens (29/10 au 06/11)**. Les comptes quotidiens indiquent **30 nouveaux essais fictifs cumulés**, **0 essai attribué à Gemini** et **30 au moteur statistique** ; les compteurs quotidiens décrivent les inscriptions enregistrées, pas 30 réussites ni 30 expériences indépendantes.
- `reports/strategy_foundry.json` : **30 hypothèses distinctes**, **0 `gemini_hypotheses`** ; `reports/strategy_forward.json` : **24 pistes actuellement suivies**, **6 archivées**, **5 transactions clôturées au total dans les pistes actives**, **0 piste à rendement net positif** au dernier instantané et **0 preuve de robustesse**.
- `reports/strategy_competition.json` : **0 candidat qualifié, 0 champion fictif, 0 promotion des 36 robots d'origine**. Plusieurs pistes devant Hold ont gardé leurs liquidités quand le marché baissait : dépasser Hold sans gain net ne démontre pas un avantage exploitable.
- `reports/robot_evolution.json` : **36 robots suivis**, dont **12 Hold intouchables**, **24 variantes de réglage en comparaison prospective** et **0 réglage activé**.
- `reports/research_director.json` : **3 plans locaux** BTC/ETH/SOL, **8 journées prospectives chacun**, en attente d'un minimum prévu de 90. Le directeur n'a créé aucun plan Gemini nouveau dans le dernier cycle.
- `reports/market_knowledge.json` : **9 journées synchronisées** de caractéristiques générales du marché au 06/11. Des historiques de cours plus anciens existent, mais ils ne remplacent pas une série chronologique de tous les indicateurs (sentiment, liquidité, actualités, transferts) collectés à dates communes.

## 3. Gemini, cache et repli quantitatif

Les rapports quotidiens contiennent des périodes `model_reflection_completed` et un échec `model_reflection_failed` daté du **5 novembre**. Une conclusion `completed` dans un bilan journalier ne prouve pas à elle seule que chaque cycle de recherche a produit une nouvelle réponse : regarder `model_last_called_at`, `used_cache`, `source` et les traces du workflow.

Dernier statut relu : `reports/ai_research_status.json` à **15:58 UTC le 06/11** indique `provider=gemini`, `state=model_reflection_completed`, **`used_cache=true`**, dernière génération enregistrée à **12:29:05 UTC** le 06/11. Le cache de 15:58 ne constitue **pas** un nouvel appel. Les propositions structurées n'ont pas conduit à des créations de stratégie Gemini dans la Foundry (0 source Gemini).

Le modèle Gemini analyse et propose des expériences narratives ; le repli quantitatif inscrit les essais réels dans les journaux, sous sa propre provenance. **Ne jamais attribuer ces essais à Gemini ou à GPT.** Aucune API OpenAI payante n'est utilisée pour les workflows.

## 4. Données on-chain et limites

`reports/large_transfer_observations.json`, 15:57:50 UTC : échantillon public **non exhaustif** de transferts Ethereum USDC/USDT, **4 gros transferts observés** dans cet échantillon récent. `reports/whale_follow.json`, 15:57:56 UTC : **4 adresses suivies**, **6 nouveaux transferts** relevés. Ces événements ne certifient ni l'identité d'une « baleine », ni un achat, ni la direction future des cours. Les 30 essais de placement inscrits sont du repli statistique, pas des essais déclenchés par ces transferts.

## 5. Acquis techniques et travaux inachevés

Acquis observés au cours de la première période : automatisation des simulations, collecte des indicateurs, recherche bornée de variantes, mémoire d'hypothèses, séparation des 12 Hold, études après frais, suivi de provenance Gemini/cache/repli. Les supervisons GPT ont audité et corrigé notamment des problèmes de diagnostic Actions (PR #3) et les consignes de recherche Gemini (PR #4). **Une CI verte n'est pas une preuve de rentabilité ni d'une disponibilité ininterrompue.**

À traiter sans toucher aux historiques :
1. **Stratégies crypto / coûts** : isoler frais, fréquence, qualité des règles et risques par comparaisons prospectives appariées ; ne pas réduire arbitrairement les frais du simulateur pour améliorer les chiffres.
2. **Créativité de la recherche** : Gemini produit peu de propositions structurées exploitables ; transformer des hypothèses narratives en protocoles réellement falsifiables et tester leur provenance.
3. **Directeur saturé** : prévoir une voie parallèle de recherche `shadow` bornée et testée, sans remplacer les trois plans locaux en cours.
4. **Valeur prédictive on-chain** : étudier séparément l'hypothèse « signal de transfert confirmé + filtre prix/volume » et un contrôle qui ignore les transferts ; dans l'état actuel, pas de causalité démontrée.
5. **Maturité des données** : accumuler des jours et des transactions authentiquement nouveaux, sans backfill inventé ni réutiliser un contrôle historique comme donnée vierge.

## 6. Conclusion de la première période

**Évolution technique : positive ; preuves de rentabilité : négatives ou insuffisantes ; amélioration autonome des robots : aucune adoptée.**

Ce document est un **bilan GPT indépendant** des données réellement enregistrées. Il ne remplace ni le rapport quotidien `reports/ai_daily_brief.json`, ni la vérification des fichiers à la date d'une lecture ultérieure. Prochain bilan hebdomadaire éventuel : réévaluer les nouveaux jours, l'évolution nette après coûts et la création effective d'expériences Gemini, sans recopier mécaniquement ces valeurs.

**Fichiers sources et accès :**
- `reports/realistic_metrics.json`, `reports/multi_asset_micro_metrics.json`
- `reports/ai_daily_brief.json`, `reports/ai_research_status.json`, `reports/ai_research_proposals.json`
- `reports/strategy_foundry.json`, `reports/strategy_forward.json`, `reports/strategy_competition.json`
- `reports/robot_evolution.json`, `reports/research_director.json`, `reports/market_knowledge.json`
- `reports/large_transfer_observations.json`, `reports/whale_follow.json`
