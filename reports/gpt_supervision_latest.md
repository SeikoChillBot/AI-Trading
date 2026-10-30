# Seiko Trading Lab — contre-analyse GPT du 30 octobre 2026

**Auteur :** ChatGPT, supervision indépendante ; ne pas attribuer ce document à Gemini.  
**Contrôle :** vendredi 30/10/2026 vers 14 h 40, heure de Paris (UTC+1).  
**Nature :** vérification des rapports GitHub et des exécutions ; aucune API GPT payante, aucun ordre réel.  
**Fraîcheur des données :** recherche publiée à 13:02:32 UTC (14:02 Paris), simulation paper à 13:34:49 UTC (14:34 Paris). Les résultats peuvent évoluer ensuite.

## 1. Gemini : vraie réponse, puis cache

- `reports/ai_research_status.json` : `state=model_reflection_completed`, `provider=gemini`, `model_last_called_at=2026-10-30T12:05:31.600322Z`, `attempts_in_slot=1`, sans erreur signalée. Le journal de l'exécution de recherche **41052681456** confirme l'étape réelle à 12:05 UTC. Ce statut et la source `gemini_generate_content` indiquent une réponse Gemini enregistrée, non un repli statistique.
- Le cycle de recherche **41059890515**, à 13:02 UTC, est **SUCCESS**, mais son rapport porte `used_cache=true` : **ce cycle n'a pas obtenu une nouvelle réponse Gemini**. Il a publié les données actualisées, commit `9ea5e54` poussé sur `main` à 13:02:36 UTC.
- Gemini a fourni **2 propositions d'expériences**, **2 propositions de seuil** (`btc_momentum`, `eth_momentum`, `entry_scale=1.2`), mais **0 `research_tasks`**, **0 `strategy_designs`**, **0 `scenario_proposals`** et **0 `desk_notes`**. C'est une analyse réellement générative, **pas** une nouvelle stratégie structurée ou un essai exécuté par Gemini.
- `reports/robot_evolution.json` : **36 robots**, **12 Hold immuables**, **24 variantes en test**, **0 activation**. Une ancienne variante `sol_momentum` conserve la provenance `gemini_structured_hypothesis` ; elle ne doit pas être attribuée à l'appel du jour.
- Le rapport quotidien du 30/10 attribue **2 nouveaux essais de placement au moteur statistique et 0 à Gemini**. Les essais existants de Gemini ne sont pas réinterprétés comme des transactions.

## 2. Audit GPT indépendant des résultats, après coûts simulés

| Famille | Départ fictif | Dernière valeur | Rendement net estimé | État de validation |
|---|---:|---:|---:|---|
| Crypto V2, 18 × 20 USD | 360 USD | **330,73541 USD** | **−8,1291 %** | **0/18** évaluable |
| Multi-actifs micro, 18 × 20 USD | 360 USD | **359,11149 USD** | **−0,2468 %** | **0/18** évaluable |

**Crypto V2 :** `reports/realistic_metrics.json`, 13:34:49 UTC : **122 ordres fictifs remplis**, **0 refus**, **58 allers-retours clôturés au total**, **18,56926 USD de frais déjà comptabilisés** (somme par stratégie), **18/18 robots en perte**. Les frais agrégés représentent environ **5,16 % des 360 USD de capitaux expérimentaux initiaux**, mais ne peuvent pas être identifiés mécaniquement comme la cause de toute la perte de 29,26459 USD. Le drawdown global observé déclaré est **8,1291 %**. Durée seulement **1,7954 jour**, contre un seuil de travail de **14 jours et 20 allers-retours par robot**. Seulement **4 stratégies** font mieux que leur Hold respectif sur cette fenêtre, tout en restant elles-mêmes en perte ; une supériorité relative ponctuelle ne prouve rien.

**Multi-actifs micro :** `reports/multi_asset_micro_metrics.json`, 13:34:49 UTC : **12 positions ouvertes**, **0 aller-retour clôturé**, durée **1,6996 jour**, seuil **30 jours et 20 allers-retours**. Les 16 scénarios actions/ETF sont marqués `DELAYED_OR_CLOSED` et les 2 EUR/USD `REFERENCE_ONLY` ; ces qualités de cotation n'impliquent pas que toutes les positions sont en cash. Fractionnement, dividendes/splits, disponibilité européenne et cours exécutables restent non vérifiés.

**Étude historique quotidienne, 8 fenêtres par actif :**

| Actif | Rendement net moyen | Excès moyen vs Hold | Rendement frais ×2 | Pire drawdown | Trades clôturés | Fenêtres devant Hold |
|---|---:|---:|---:|---:|---:|---:|
| BTC | −1,5586 % | +2,8004 points | −3,8579 % | 19,5062 % | 9 | 5/8 |
| ETH | **+7,3968 %** | +5,4038 points | **+5,0781 %** | **25,1673 %** | 7 | 4/8 |
| SOL | −4,9151 % | −0,0277 point | −8,9099 % | 35,0085 % | 16 | 4/8 |

**Lecture correcte :** ETH a une moyenne historique positive, donc « tous les rendements historiques sont négatifs » serait faux. Mais **aucun candidat n'est robuste** : nombre de trades insuffisant, résultats non uniformes selon les fenêtres, drawdown ETH >20 %, et risque de sélection répétée des mêmes historiques. Les seuils sont des garde-fous de recherche, non une certification.

**Étude horaire distincte** (`reports/intraday_research.json`, bougie 12:00 UTC) : moyennes historiques **BTC −7,85458 %**, **ETH −10,22239 %**, **SOL −8,56586 %** ; toutes trois ont un excès moyen négatif face au Hold. Les trois pistes horaires prospectives sont également négatives (**BTC −5,12025 %**, **ETH −3,30195 %**, **SOL −0,4286 %**) avec **33 observations et 1 trade clôturé chacune**. Cela explique pourquoi le bilan quotidien peut annoncer « 0 avec un excès historique positif » **pour les études horaires** sans contredire les valeurs quotidiennes ci-dessus. Ne pas fusionner ces protocoles.

## 3. Compléments critiques aux propositions Gemini

**Proposition BTC « frais doublés » :** Gemini demande un simple achat spot fictif de 20 USD conservé sept jours, avec frais doublés, pour juger des **robots de momentum**. Ce protocole ne teste pas directement le signal momentum : il mesure surtout une détention ponctuelle avec coût différent. **Expérience corrigée à préparer, non lancée :** figer un robot momentum et son clone à règles et bougies identiques, l'un aux frais de base et l'autre aux frais ×2, plus un Hold synchronisé, sur **de nouvelles données**. Comparer rendement net, différence vs Hold, nombre de signaux/trades, drawdown et coûts ; rejeter l'avantage si le clone perd son excès net. Aucune nouvelle série prospective indépendante n'est encore disponible pour conclure.

**Proposition SOL « breakout » :** un achat spot de trois jours déclenché par `market_selloff` ou `sampled_large_transfer` ne suffit pas à tester un **filtre breakout**. Un transfert de stablecoins échantillonné, notamment sur Ethereum, ne prouve ni achat SOL ni flux directionnel. **Expérience corrigée à préparer, non lancée :** comparer sur les mêmes futurs jours une règle breakout déclarative et figée, un témoin Hold et un témoin sans filtre ; mesurer faux signaux selon une définition préalable, frais, drawdown et rendement net. Ne pas utiliser de transfert comme preuve de signal.

**Propositions de réglage `entry_scale=1.2` :** il s'agit d'un **seuil de signal**, non d'une réduction du montant engagé ni d'une diminution démontrée du risque. Le système les laisse au stade d'hypothèses ; aucun robot n'a été modifié.

## 4. Travaux autonomes non terminés et limite de conception

- `reports/strategy_foundry.json` : **18 hypothèses**, **0 hypothèse Gemini**, **3 optimisations**, **3 évolutions**, **6 croisements**, **3 plans du directeur**, **0 contrôle contradictoire local associé à Gemini**. `reports/scientific_memory.json` : 18 hypothèses archivées ; **18/18** échouent au contrôle historique de frais doublés, **17/18** à la positivité nette, **14/18** au volume de trades, sur des historiques déjà exploités.
- `reports/strategy_forward.json` : **18 pistes prospectives**, **1 journée observée chacune**, **0 trade clôturé**, **0 championne** (`strategy_competition.json`). Les écarts favorables vs Hold de certaines pistes restées en liquidités pendant la baisse ne sont pas une preuve de stratégie rentable.
- `reports/research_director.json` : **3 plans locaux BTC/ETH/SOL**, chacun à **1 jour prospectif**, **0 plan neuf Gemini** et **0 paire contradictoire**.
- **Goulot de conception vérifié dans `research/research_director.py` :** tant que le plan actif d'un actif est `awaiting_prospective_data`, le directeur le conserve et passe à l'actif suivant **avant** d'examiner les éventuelles nouvelles `research_tasks` Gemini. Les trois emplacements locaux sont actuellement occupés. Même si Gemini produisait demain une tâche structurée, elle pourrait attendre longtemps sans voie expérimentale parallèle. **Correction proposée, pas appliquée :** une file d'attente/voie `shadow` indépendante et bornée pour de nouveaux plans Gemini, avec gel horodaté, provenance, quotas de slots, comparaison synchronisée, tests anti-fuite et aucun écrasement des plans en cours. Ne pas faire une modification rapide de ce moteur sans tests ciblés.

## 5. Journal de scénarios et couverture de marché

- `reports/ai_placement_experiments.json` : **11 essais enregistrés**, dont **9 actifs** et **2 terminés mais non validés** (1 jour : SOL **−8,4353 %**, ETH **−6,2927 %** en valorisation fictive). Plusieurs horizons 1/3/7 jours réutilisent les **mêmes entrées et observations** : ils ne constituent **pas** des échantillons indépendants. Deux essais du 30/10 sont encore `waiting_next_closed_day` et ne disposent pas de prix d'entrée.
- `reports/market_pulse.json` : dernière journée Kraken entièrement close **29/10** ; variations 7 jours BTC **−4,324 %**, ETH **−5,745 %**, SOL **−7,862 %** ; volatilité annualisée descriptive 30 jours BTC **29,3 %**, ETH **36,99 %**, SOL **42,42 %**. Ces constats ne prédisent pas le lendemain.
- `reports/base_usdc_observations.json` est maintenant `state=observing` : **809 événements échantillonnés**, **0 gros transfert dans cet échantillon**, une seule source RPC indiquée, couverture **12 derniers blocs uniquement**. **L'ancienne panne Base ne doit plus être présentée comme toujours active**, mais ce très court échantillon ne couvre pas toute la chaîne.
- `reports/market_news.json` : 9 titres de presse, **non vérifiés éditorialement**, certains publiés après l'appel Gemini de 12:05 UTC. Aucun lien causal avec les variations ni ordre de trading ne doit être inféré de ces titres.

## 6. Infrastructure, sécurité et modifications réelles

- Recherche **41059890515** : **SUCCESS**, tests et assemblage de site réussis, **publication Git confirmée** à 13:02:36 UTC (`9ea5e54`). Dernier Paper **41064399358** : **SUCCESS**, 13:34–13:34 UTC, résultats publiés commit `2912fee`. Pages **41064435229** : **SUCCESS** ; watchdog **41064452577** : **SUCCESS**. Le snapshot `system_health.json` à 13:02 disait encore « research running », mais le run s'est terminé ensuite avec succès : il est temporellement périmé sur ce point, pas signe de panne.
- Workflow `.github/workflows/research.yml` : `SEIKO_AI_PROVIDER: gemini` et seul secret IA transmis `GEMINI_API_KEY` ; **aucune clé OpenAI transmise à ce workflow**. Les tests incluent l'absence de repli payant. Le statut de facturation réel du projet Google **ne peut pas être prouvé par ces fichiers** : le vérifier dans AI Studio, sans activation payante.
- Avertissements GitHub sur dépréciation Node.js 20 dans certaines actions, **non bloquants** dans les runs observés. Aucun correctif urgent à faire sans préparer et tester une montée de version.
- **Action effectuée par GPT aujourd'hui :** lecture des sources, recoupement des données et des journaux, contre-analyse et mise à jour de ce rapport uniquement. **Aucun changement** des moteurs, paramètres, 36 historiques, témoins Hold, interface, workflows ou secrets. Aucun test local du moteur n'a été exécuté par GPT ; les résultats CI cités sont des tests réellement exécutés par GitHub Actions.

## 7. Priorités proposées

1. Préparer une voie `shadow` Gemini parallèle et strictement bornée pour éviter la saturation du directeur, **sur branche isolée avec tests de provenance, idempotence et chronologie**, sans toucher aux expériences existantes.
2. Convertir les deux expériences narratives Gemini en **protocoles appariés réellement falsifiables** (momentum frais ×2 et breakout vs témoins), puis les enregistrer comme **propositions non exécutées** jusqu'à disponibilité de nouvelles bougies.
3. Accumuler des journées et transactions prospectives réellement nouvelles ; refuser toute promotion sur le seul historique ou sur une journée de baisse.
4. Continuer la supervision de la provenance Gemini/cache/repli et la vérification de publication Git ; préserver l'absence de facturation OpenAI et d'ordres réels.

## Sources GitHub contrôlées

- [Rapport Gemini et statut](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/ai_research_status.json) ; [propositions](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/ai_research_proposals.json) ; [bilan](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/ai_daily_brief.json).
- [Crypto V2](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/realistic_metrics.json) ; [multi-actifs micro](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/multi_asset_micro_metrics.json) ; [Foundry](https://github.com/SeikoChillBot/AI-Trading/blob/main/reports/strategy_foundry.json) ; [directeur](https://github.com/SeikoChillBot/AI-Trading/blob/main/research/research_director.py).
- [Recherche 41059890515](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41059890515) ; [Paper 41064399358](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41064399358) ; [Pages 41064435229](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41064435229).
