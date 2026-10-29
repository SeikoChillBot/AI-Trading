# Seiko Trading Lab — contre-analyse GPT du 29 octobre 2026

**Auteur :** supervision ChatGPT, indépendante de Gemini et des moteurs statistiques.  
**Périmètre :** dépôt GitHub `SeikoChillBot/AI-Trading`, données fictives uniquement.  
**Date du contrôle :** 29/10/2026, vers 14 h 05 (Europe/Paris).  
**Sources internes :** `reports/ai_research_status.json`, `reports/ai_research_proposals.json`, `reports/ai_daily_brief.json`, `reports/realistic_metrics.json`, `reports/multi_asset_micro_metrics.json`, `reports/challenger_walkforward.json`, `reports/robot_evolution.json`, `reports/ai_placement_experiments.json`, `reports/base_usdc_observations.json`, `reports/whale_follow.json` et exécutions GitHub Actions mentionnées ci-dessous.

## 1. Statut réellement vérifié de Gemini

- Une **réponse générative Gemini réelle** a été enregistrée à **08:54:51 UTC** le 29/10 : `model_reflection_completed`, `source=gemini_generate_content`, `model_last_called_at=2026-10-29T08:54:51Z`.
- Le rapport de recherche du cycle **11:44–11:45 UTC** réutilise cette réponse : `used_cache=true`, `review_slot=2026-10-29T06:00Z`. Ce cycle est **une actualisation des observations, pas un nouvel appel Gemini**.
- Le workflow recherche [40867717628](https://github.com/SeikoChillBot/AI-Trading/actions/runs/40867717628) et le workflow Paper [40877852892](https://github.com/SeikoChillBot/AI-Trading/actions/runs/40877852892) sont tous deux `success`. Le déploiement Pages [40877890544](https://github.com/SeikoChillBot/AI-Trading/actions/runs/40877890544) est `success`.
- Gemini a émis **2 expériences historiques non testées** et **3 hypothèses de réglage** dans son JSON. Le journal des robots n'enregistre qu'**une variante Gemini en test prospectif**, `sol_momentum`; aucun réglage n'est validé. Les **9 scénarios de placement fictif** sont tous issus du moteur quantitatif, **zéro** d'une décision Gemini.

## 2. Audit indépendant GPT — performances et risques

### Expérience prospective crypto (18 robots × 20 USD fictifs)

**Dernière observation : 12:59:26 UTC.** Capital initial 360 USD ; valorisation estimée **347,86669 USD**, soit **−12,13331 USD (−3,3704 %)**. Frais déjà comptabilisés dans les stratégies : **8,1169 USD** (somme des `fees_paid_usd`), sans prétendre que la perte est entièrement imputable aux frais. **52 ordres fictifs remplis, zéro refusé**, mais seulement **0 robot évaluable** : durée **0,7709 jour**, seuil de revue 14 jours et au moins 20 allers-retours clôturés par stratégie.

Sur les 18 robots, **16 affichent une performance négative et 2 restent à 0 %**, aucun n'est positif. **Six surpassent néanmoins leur témoin Hold en points de rendement** sur la fenêtre observée, parfois simplement en restant en liquidités : cela ne démontre pas un avantage exploitable. Le meilleur classement relatif et le rendement absolu doivent rester distincts. La valorisation reste une simulation avec frais, carnet instantané et glissement hypothétique.

### Expérience prospective multi-actifs micro (18 robots × 20 USD fictifs)

**Dernière observation : 12:59:26 UTC.** Capital initial 360 USD ; valorisation **359,8605 USD**, soit **−0,1395 USD (−0,0387 %)**. Durée **0,675 jour**, **0 robot évaluable** (seuil 30 jours et 20 allers-retours). Les 16 robots actions/ETF présentent des cotations `DELAYED_OR_CLOSED` et sont encore en cash ; seuls les 2 scénarios EUR/USD ont une référence `REFERENCE_ONLY`, non exécutable chez un courtier. **Le résultat quasi stable ne signifie donc pas que 16 stratégies ont résisté au marché.** Les fractions d'actions/ETF restent des hypothèses de recherche non confirmées pour un compte français.

Les deux groupes de 360 USD sont des **expériences distinctes**, pas une somme à investir, et leurs résultats ne doivent pas être fusionnés comme un portefeuille réel.

### Étude historique walk-forward (BTC / ETH / SOL, 8 fenêtres OOS chacune)

| Actif | Rendement net moyen historique | Excès moyen vs Hold (points) | Frais ×2 : moyenne | Baisse maximale observée | Allers-retours clôturés |
|---|---:|---:|---:|---:|---:|
| BTC | −2,6699 % | +0,8265 | −5,3474 % | 19,5062 % | 11 |
| ETH | **+7,8287 %** | +4,3323 | **+5,5104 %** | **25,1673 %** | 7 |
| SOL | −5,2159 % | −2,5300 | −9,0164 % | 35,0085 % | 15 |

**Correction importante de la synthèse Gemini :** dire que les performances nettes historiques sont « négatives » pour tous les robots/actifs est **faux pour cette étude ETH**, dont la moyenne est positive. Cela ne qualifie **pas** ETH : 7 trades clôturés (<20), seulement **4 fenêtres sur 8** battent Hold, **3 sur 8** ont un rendement net positif, et le drawdown maximal dépasse le seuil de travail de 20 %. La moyenne positive peut être tirée par quelques fenêtres très favorables. Les mêmes fenêtres déjà explorées ne constituent pas une nouvelle preuve indépendante.

BTC : moyenne nette négative, frais doublés négatifs, 11 trades et seulement 4/8 fenêtres devant Hold. SOL : moyenne nette négative, baisse maximale 35 %, 15 trades et 3/8 fenêtres devant Hold. **Aucun des trois candidats ne satisfait les critères de qualification.**

## 3. Vérification des hypothèses et de l'attribution

- Le JSON Gemini propose notamment `entry_scale=1.2` en parlant de « réduction de l'exposition ». **C'est un contresens dans la justification** : dans `research/robot_tuning.py` et les consignes révisées, ce multiplicateur concerne le **seuil de signal**, pas le montant investi ni une baisse garantie du risque. Les explications de vulnérabilité technique dans une autre proposition ne sont pas étayées par les preuves transmises. Ces propositions restent **non validées**.
- Les expériences suggérées par Gemini (stress des frais BTC, fenêtres indépendantes ETH) sont **des hypothèses non testées**, et non des tests terminés. Leur exécution doit préserver des données réellement nouvelles et un protocole falsifiable.
- `reports/robot_evolution.json` compte **36 robots**, dont **12 témoins Hold immuables**, **21 variantes en test** (20 statistiques, 1 Gemini), 3 en analyse et **0 adoption**. Les protections prospectives doivent rester en place.
- `reports/ai_placement_experiments.json` : 9 essais quantitatifs fictifs, 6 positions en attente de nouveaux jours clôturés et 3 entrées encore en attente. Les 6 positions ont **zéro observation après entrée** ; leurs valeurs provisoires ne sont pas des performances finales. Aucun essai initié par Gemini.
- `reports/whale_follow.json` signale **un transfert public USDC nominal d'environ 1,8 M USD** observé sur Ethereum à 11:02:35 UTC ; ni identité du propriétaire, ni achat/vente ne sont établis. Les quatre adresses suivies ne constituent pas une couverture exhaustive.

## 4. Incident technique distinct : Base USDC

Le rapport `reports/base_usdc_observations.json` à **11:44:52 UTC** reste **`state=unavailable`** : 0 événement observable, et non « aucun transfert ». Les tentatives RPC ont échoué sur **PublicNode (ValueError)**, **Nodely (ValueError)** et **RPC officiel Base (HTTPError)**. Les tests unitaires simulés du workflow recherche sont verts, **mais la collecte réelle Base n'est pas opérationnelle**.

**Diagnostic limité :** le code `research/base_usdc_watch.py` masque les détails des erreurs JSON-RPC derrière `ValueError`; impossible de conclure s'il s'agit d'une méthode refusée, d'une limite de plage, d'une réponse inattendue ou d'une indisponibilité fournisseur. Recommandation : journaliser de manière bornée le **code d'erreur RPC non sensible** et la méthode concernée, sans URL de clé ni corps brut, puis valider sur un vrai cycle. Ne pas activer d'API Blockscout payante.

## 5. Correctif réellement appliqué aujourd'hui

Le workflow `.github/workflows/research.yml` a été **verrouillé sur `SEIKO_AI_PROVIDER: gemini`**, et les variables `SEIKO_AI_MODEL` ainsi que `OPENAI_API_KEY` ont été **retirées de son environnement** (commit `c9f89766da84c95f1f11edd9bb4498b0bb4e8ff7`). Les étapes de recherche, tests, simulation et publication ont été conservées. **Vérification statique après écriture : réussie** ; **aucun nouveau run complet sous ce commit n'était encore confirmé** au moment du contrôle. La facturation du projet Gemini n'est pas vérifiable depuis ces rapports : la gratuité effective de la clé dépend toujours du niveau du projet Google.

## 6. Suite proposée — sans argent réel ni API GPT payante

1. **Ne promouvoir aucun robot** avant les seuils prospectifs, le contrôle des frais, la comparaison au Hold et des échantillons indépendants.
2. Lors du prochain cycle Gemini non mis en cache, vérifier que la synthèse distingue correctement le **+7,8287 % historique ETH** des critères de qualification non satisfaits et que les multiplicateurs de seuil ne sont plus décrits comme des montants.
3. Corriger le diagnostic Base **sans ajouter de fournisseur payant**, puis attendre un succès réel pour annoncer le suivi opérationnel.
4. Recontrôler l'exécution de `research.yml` après le verrouillage Gemini, la fraîcheur des rapports et les scénarios lorsque de nouveaux jours de marché seront effectivement clôturés.

**Aucun ordre réel, aucun changement de stratégie approuvé, aucun historique de robot ou témoin Hold modifié par cette supervision.** Cette note est une **contre-analyse GPT** : elle ne doit pas être attribuée à Gemini ni présentée comme une preuve de rendement futur.
