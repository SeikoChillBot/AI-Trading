# Seiko Trading Lab — supervision indépendante GPT du 1er novembre 2026

**Auteur :** ChatGPT, contre-analyse distincte de Gemini.  
**Contrôle :** dimanche 01/11/2026, vers 14 h 11 Europe/Paris (UTC+1).  
**Périmètre :** rapports réellement publiés sur `main`, code et journaux GitHub Actions. Toutes les expériences sont fictives (20 USD théoriques maximum par scénario) ; aucune API GPT payante ni ordre réel.

## 1. Gemini : appel réel à 10 h 02, cache à 12 h 47

- `reports/ai_research_status.json` et `reports/ai_research_proposals.json`, générés **11:47:46 UTC (12:47 Paris)** : `state=model_reflection_completed`, `provider=gemini`, `source=gemini_generate_content`, `model_last_called_at=2026-11-01T09:02:29Z`, **`used_cache=true`** pour ce dernier cycle. Le run de recherche **41303362835** a réussi et publié les rapports ; **il n'a pas généré une nouvelle réponse Gemini à 11:47**.
- Le run de recherche **41291256182** (09:01–09:02 UTC) montre l'étape Gemini achevée et le statut `model_reflection_completed` avec deux tentatives consignées dans le créneau ; il corrobore la réponse Gemini enregistrée à **09:02 UTC (10:02 Paris)**. Le champ `last_http_status=null` dans le dernier snapshot n'est **pas** une preuve d'échec. Aucun repli statistique ne doit être présenté comme une réponse Gemini.
- **Contenu réel de la réponse conservée :** 1 expérience narrative BTC, 1 hypothèse de seuil `btc_scalp_conservative entry_scale=1.2`, **0 `research_tasks`**, **0 `strategy_designs`**, **0 `scenario_proposals`**, **0 `desk_notes`**. Aucun paramètre n'a été activé. Le seuil proposé modifie la condition d'entrée, pas le capital engagé.
- L'expérience BTC décrit un **achat spot fictif de trois jours sur `market_selloff`** pour conclure sur un **signal breakout**. Ce n'est pas un test du breakout : ni déclencheur breakout défini, ni comparaison à une règle sans filtre sur les mêmes dates. **Complément GPT non exécuté :** figer avant observation une règle breakout déclarative et une règle témoin sans filtre, comparer aux mêmes futurs jours et au Hold, sous frais normaux/doublés, en contrôlant nombre de trades, net, excès vs Hold et drawdown. Une seule détention de trois jours ne permet pas de qualifier la stratégie.

## 2. Les 36 robots : données après frais et risque

Dernière simulation Paper vérifiée **01/11 à 13:06:10 UTC (14:06 Paris)** ; run **41309599176 SUCCESS**, site Pages **41309620227 SUCCESS**.

| Cohorte indépendante | Départ fictif | Valeur publiée | Rendement | Évaluable |
|---|---:|---:|---:|---:|
| Crypto, 18 × 20 USD | 360 USD | **318,84824 USD** | **−11,4310 %** | **0/18** |
| Multi-actifs, 18 × 20 USD | 360 USD | **355,65678 USD** | **−1,2064 %** | **0/18** |

**Crypto :** `reports/realistic_metrics.json` : **3,7755 jours**, **205 ordres fictifs remplis**, **99 allers-retours clôturés au total**, **29,83739 USD de frais cumulés déjà comptabilisés**, **18/18 robots en perte**, **drawdown maximal agrégé observé 11,5068 %**. Les frais représentent **8,29 %** du capital de départ, mais ne doivent pas être assimilés à toute la perte ni soustraits une seconde fois. Seulement **2 des 15 stratégies non-Hold** dépassent leur témoin Hold respectif, et les deux restent en perte. Le meilleur rendement ponctuel est `btc_scalp_conservative` à **−1,8205 %** (1 aller-retour) ; le pire `sol_bollinger` à **−26,9099 %** (13 allers-retours, 0 gagnant). **Aucun résultat qualifié** : seuil de travail 14 jours et 20 allers-retours **par robot**, pas cumulés.

**Multi-actifs :** `reports/multi_asset_micro_metrics.json` : **3,6797 jours**, **0/18 évaluable**, seuil 30 jours et 20 allers-retours par robot ; cotations actions/ETF retardées ou marchés fermés, EUR/USD de référence non exécutable, dividendes et opérations sur titres non intégrés. Le montant multi-actifs est un **autre portefeuille fictif** : ne pas additionner les performances comme si les deux cohortes étaient un seul investissement.

**Historique quotidien (8 fenêtres par actif, différent des études horaires) :**

| Actif | Rendement net moyen | Excès moyen vs Hold | Net avec frais ×2 | Pire drawdown | Trades clôturés |
|---|---:|---:|---:|---:|---:|
| BTC | −1,7929 % | +2,9651 points | −4,3416 % | 19,5062 % | 8 |
| ETH | **+7,1425 %** | +6,4566 points | **+4,6268 %** | **25,1673 %** | 7 |
| SOL | −5,4751 % | −0,1636 point | −9,2417 % | 35,0085 % | 14 |

ETH conserve un historique moyen positif mais **échoue** au nombre de trades et au seuil de drawdown (<20 %) ; le fait de dépasser Hold dans 5/8 fenêtres ne suffit pas. Aucun candidat validé ; risque de surajustement des historiques déjà explorés.

## 3. Recherche autonome : provenance et maturité

- `reports/strategy_foundry.json` : **18 hypothèses**, **0 issue de Gemini**, 3 optimisations, 3 évolutions, 6 croisements, 3 plans locaux ; mémoire scientifique : **18/18** échouent au critère historique de frais doublés, **16/18** au rendement net positif et **14/18** au nombre de trades.
- `reports/strategy_forward.json` : **18 pistes fictives, 3 vrais jours prospectifs chacune**, **1 aller-retour clôturé au total**, **0 championne**. Le plan local SOL `mean_reversion` est à **−10,88235 %**, 1 trade, drawdown 10,88235 %, excès vs Hold **−2,36063 points**. Les stratégies à 0 % qui sont restées en cash pendant une baisse peuvent afficher un excès positif vs Hold, **sans démontrer un avantage reproductible**.
- `reports/research_director.json` : 3 plans actifs **locaux** BTC/ETH/SOL, 3/90 jours prospectifs, 0 plan Gemini structuré, 0 contrôle rival effectivement lancé. Le directeur privilégie les anciens plans `awaiting_prospective_data` avant de regarder une nouvelle tâche Gemini : **goulot toujours présent**. Une voie expérimentale parallèle `shadow` bornée reste à concevoir et à tester sur branche ; **pas de modification précipitée de ce moteur aujourd'hui**.
- `reports/ai_placement_experiments.json` : **16 essais retenus**, 9 actifs et 7 achevés **non validés** ; **100 % `actor=quantitative_auto_fallback`**, **0 essai Gemini**. Plusieurs horizons 1/3/7 jours partagent les mêmes entrées et ne sont pas des observations indépendantes. Bilan quotidien du 01/11 en cours : **4 nouveaux essais statistiques**, 0 Gemini.

## 4. Anomalie opérationnelle confirmée et correction réellement fusionnée

**Problème observé :** `reports/system_health.json` (11:47 UTC) affichait la recherche GitHub `unknown` (« No completed run in recent GitHub history »), alors que **41303362835** était **SUCCESS** à 11:47 UTC. `research/ops_status.py` interrogeait seulement les **35 dernières exécutions de tous les workflows confondus** ; les cycles Paper, Pages et watchdog fréquents noyaient les recherches. **C'était un faux inconnu, pas une panne Gemini.**

**Correction appliquée :** PR **#3**, fusionnée sur `main` au commit **`6731f0485c46c5232b25f2cb5717762403d78457`** :
- `ops_status.py` interroge désormais séparément les derniers runs de `simulate.yml` et `research.yml`, plutôt qu'une liste globale saturée.
- Si une API workflow échoue, l'autre statut reste lisible et le diagnostic devient `partial` plutôt qu'une panne générale fabriquée.
- Tests de non-régression ajoutés dans `tests/test_ops_status.py` et inclus dans la CI isolée ; **branche 41309907395 SUCCESS**, puis **validation `main` 41309967234 SUCCESS** (syntaxe, tests, smoke-test de recherche, garde-fou paper-only).
- **Limite de vérification :** l'exécution suivante de `research/ops_status.py` sur les vraies réponses GitHub **après fusion** n'était pas encore publiée au moment du contrôle. La CI teste le correctif avec réponses simulées ; ne pas affirmer un résultat de bout en bout avant un nouveau `reports/system_health.json`.

Ce correctif n'a modifié **ni stratégie, ni 36 robots, ni Hold, ni historiques, ni interface, ni secrets**. Il améliore la fiabilité de la supervision, **pas la rentabilité**.

## 5. Marché et limites des sources

- Dernière journée Kraken clôturée dans `reports/market_pulse.json` : **31/10/2026**, variations sept jours BTC **−4,129 %**, ETH **−4,375 %**, SOL **−6,778 %**. Données descriptives, non prédictives.
- Surveillance Ethereum : 300 transferts USDC/USDT échantillonnés, 0 gros transfert dans cet échantillon ; Base : **624 événements sur 12 blocs seulement**, 0 gros transfert observé. Couverture non exhaustive, aucune identification de baleine ni achat confirmé.
- Les titres RSS du journal d'actualité restent **non vérifiés éditorialement** ; ne pas transformer un titre en événement confirmé ni en signal.
- Workflow recherche `SEIKO_AI_PROVIDER=gemini`, seul secret `GEMINI_API_KEY` transmis ; **aucune clé OpenAI transmise**. Le statut de facturation Free Tier du projet Google reste **inaccessible** via GitHub.

## 6. Priorités vérifiables

1. Contrôler le prochain `system_health.json` publié après fusion PR #3 pour confirmer `research=healthy` quand le dernier run a réussi.
2. Concevoir et tester sur branche une file `shadow` de plans Gemini bornée, avec provenance, témoins synchronisés, idempotence, aucun écrasement des trois plans existants, aucun ordre réel.
3. Transformer les expériences narratives Gemini en règles déclaratives falsifiables **avant** observation ; aucun raccourci de validation sur une détention de trois jours.
4. Accumuler des observations nouvelles ; ne promouvoir aucune stratégie sur 3 jours de suivi, 1 trade ou un simple écart relatif vs Hold.

## Liens de preuve

- Recherche Gemini [09:02 UTC](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41291256182) ; recherche publiée [11:47 UTC](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41303362835) ; [Paper 13:06 UTC](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41309599176).
- [PR #3](https://github.com/SeikoChillBot/AI-Trading/pull/3) ; [CI branche](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41309907395) ; [CI main](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41309967234).
- [Rapports Gemini](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/ai_research_proposals.json), [robots crypto](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/realistic_metrics.json), [directeur](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/research_director.json), [scénarios](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/ai_placement_experiments.json).
