# Seiko Trading Lab — supervision indépendante GPT du 2 novembre 2026

Auteur : ChatGPT (analyse indépendante, distincte de Gemini). Contrôle effectué le lundi 02/11/2026 vers 14 h 28–14 h 32 Europe/Paris. Toutes les expériences et portefeuilles cités sont fictifs ; aucun ordre réel ni API GPT payante.

## 1. Gemini : réponse authentique puis cache, et limite de contenu

- Dernière réponse réellement générée : **2026-11-02T06:16:40Z**, soit **07 h 16 à Paris**, `provider=gemini`, `source=gemini_generate_content`, `state=model_reflection_completed`, `used_cache=false` au moment de cet appel.
- Dernier cycle de recherche publié : **2026-11-02T11:47:29Z** (12 h 47 Paris), `used_cache=true` et `model_last_called_at` inchangé. Il s'agit de la **même** réponse, non d'une nouvelle réflexion à 12 h 47. Workflow GitHub [recherche #41439498444](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41439498444) **SUCCESS** ; journaux du job consultés : tests, recherche, publication Git réussis.
- Contenu Gemini vérifié : **2 expériences narratives** (BTC résistance aux frais ; ETH filtre de volatilité), **0 `scenario_proposals`**, **0 `strategy_designs`**, **0 `research_tasks`**, **0 ajustement de robot**. Les 2 essais du 02/11 comptabilisés dans le bilan quotidien proviennent du **`quantitative_auto_fallback`**, pas de Gemini.
- Erreur conceptuelle BTC : « doubler les frais améliore la sélectivité » est faux si les règles d'entrée ne changent pas ; les frais modifient le rendement net, pas le déclenchement des ordres. L'achat spot de sept jours proposé ne mesure pas le comportement d'une stratégie breakout.
- Limite ETH : un achat spot de trois jours « conditionné par une volatilité calme » sans stratégie témoin simultanée ne démontre ni l'efficacité du filtre ni une baisse de drawdown. Protocole GPT proposé, non exécuté : comparer filtre / sans filtre / Hold sur les mêmes bougies futures, frais identiques puis doublés, et pré-enregistrer seuils et critères de rejet.

## 2. Portefeuilles fictifs : performance nette et risque

Dernier relevé `realistic_metrics.json` **2026-11-02T13:21:52Z** (14 h 21 Paris) :

| Groupe indépendant | Capital initial | Valeur | Rendement | Qualifiés |
| --- | ---: | ---: | ---: | ---: |
| 18 robots crypto | 360 USD | 311,36195 USD | −13,5106 % | 0/18 |
| 18 robots multi-actifs micro | 360 USD | 355,65678 USD | −1,2064 % | 0/18 |

- Crypto : **259 ordres fictifs**, **36,56767 USD de frais cumulés**, soit **10,16 % du capital initial** en frais nominaux cumulés ; perte de valorisation de **48,63805 USD** déjà nette de ces frais. Les frais représentent un montant équivalent à environ **75 % de la perte**, sans permettre de leur attribuer causalement cette proportion (les ordres/prix auraient changé dans un autre système).
- Crypto : drawdown maximal observé du groupe **13,5106 %** ; **0 stratégie active positive** ; seulement **4/15 stratégies actives** dépassent leur Hold correspondant, tout en restant négatives. Les témoins crypto BTC, ETH, SOL sont respectivement à **−5,6958 %, −4,5237 %, −9,1797 %**. Exemple : `btc_scalp_conservative` **−1,8205 %**, excès **+3,875 points** contre son Hold, mais seulement **1 aller-retour** : ce n'est pas une preuve de rentabilité.
- Multi-actifs : **0 aller-retour clôturé**, 16/18 cotations `DELAYED_OR_CLOSED` et 2/18 `REFERENCE_ONLY` ; frais modélisés **0,24973 USD** ; actions d'entreprise, fractions et FX non pleinement exécutables. La valeur n'est pas un prix de liquidation garanti.
- Depuis le contrôle du 01/11 (318,84824 USD crypto), le groupe crypto a perdu environ **7,48629 USD fictifs** supplémentaires. Ce mouvement n'est pas causé par la supervision GPT, qui n'a modifié aucun robot.

## 3. Comparaisons Hold, études historiques et données prospectives

- `reports/challenger_walkforward.json` : huit fenêtres historiques par actif. BTC : moyenne nette **−2,0280 %**, **9 transactions clôturées** ; ETH : **+6,0576 %**, **7 transactions**, drawdown maximum **25,1673 %** ; SOL : **−5,2422 %**, **15 transactions**, drawdown maximum **35,0085 %**. Ces fenêtres historiques sont déjà utilisées par la recherche ; elles ne constituent pas une validation vierge. Le résultat ETH positif ne doit pas être effacé ni promu en avantage robuste.
- `reports/intraday_research.json` : études horaires BTC/ETH/SOL avec excès historiques moyens vs Hold négatifs, respectivement **−1,493**, **−4,567**, **−4,325 points** ; ne pas les confondre avec les études quotidiennes.
- `reports/strategy_forward.json` : **18 pistes**, **4 nouvelles journées prospectives chacune**, **3 transactions clôturées cumulées**, **0 candidate qualifiée**. **16/18** pistes présentent un excès positif face au Hold sur ces quatre jours, mais **0/18** un rendement net positif : plusieurs sont restées en liquidités pendant une baisse. Cette supériorité relative de court terme n'est pas un alpha démontré ; les pistes partagent aussi des bougies et ne sont pas 18 observations indépendantes.
- `reports/research_director.json` : trois plans locaux BTC/ETH/SOL, **4/90 journées** prospectives chacun, **0 nouveau plan Gemini**, **0 paire rivale Gemini** ; les trois slots restent occupés, ce qui bloque l'accueil de futures tâches structurées. Une voie `shadow` indépendante, bornée, testée et non destructive demeure une proposition **non implémentée**.
- `reports/ai_placement_experiments.json` : **18 essais** depuis le début, **9 terminés mais non validés**, **9 actifs**, **tous issus du repli statistique**. Les essais à horizons différents peuvent réutiliser la même entrée ; ne pas les traiter comme observations indépendantes.
- `reports/robot_evolution.json` : **36 robots**, dont **12 Hold immuables**, **24 variantes en test**, **0 activation**.

## 4. Étude générale de marché : enrichissement réel mais insuffisant

- `reports/market_knowledge.json` : **5 journées UTC distinctes** de relevés datés, pas cinq années. Les prix Kraken historiques existent par ailleurs mais la série conjointe sentiment/liquidité/actualités est encore trop courte pour une relation statistique crédible.
- Dernière journée Kraken entièrement clôturée : **01/11**. Variations 30 jours descriptives BTC **−7,413 %**, ETH **−14,833 %**, SOL **−20,410 %** ; volatilité annualisée descriptive 30 jours respectivement **29,08 %**, **36,98 %**, **42,50 %**. Sentiment `Fear & Greed` **37 (Fear)** au relevé ; aucun indicateur ne prédit à lui seul la prochaine journée.
- Veille RSS BCE/CoinDesk et surveillance de transferts publics actives ; titres éditeurs non vérifiés, et **2 gros transferts observés dans un échantillon non exhaustif de 300 transferts** USDC/USDT. Ce ne sont pas des achats/ventes confirmés.
- Recherche GPT recommandée : comparer ultérieurement les règles sous régimes tendance/volatilité/sentiment/liquidité, avec périodes futures synchronisées, coûts, variables de confusion, Hold et abstention ; ne pas inventer de corrélation à partir de cinq jours.

## 5. Correction technique du jour : consignes Gemini (fusionnée, testée sur branche)

Le prompt `research/ai_reflection.py` disait à tort que toute proposition de test JSON était automatiquement exécutée et demandait jusqu'à trois expériences alors que la validation est bornée à deux. Il laissait également passer des protocoles où doubler les frais était présenté comme un changement de sélectivité.

Correction réellement fusionnée via [PR #4](https://github.com/SeikoChillBot/AI-Trading/pull/4), commit **`3c032a9f9be49abb0f903f6fcb9ea5983f133a77`** :
- Demande explicitement à Gemini d'étudier les régimes de marché, les mécanismes hypothétiques, les variables de confusion et les observations futures réfutables, au lieu de commenter seulement les pertes.
- Distingue clairement `experiments` narratifs non exécutés et `scenario_proposals`, `strategy_designs`, `research_tasks` structurés pouvant être simulés **uniquement après validation et si les places/données le permettent**.
- Corrige la limite narrative à deux, signale que frais augmentés ne changent pas la sélectivité et qu'un achat spot isolé ne teste pas un filtre de stratégie.
- Ajoute un test de non-régression au directeur. [CI isolée branche #41453159689](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41453159689) **SUCCESS** : tests, syntaxe, simulation sur snapshots et garde-fous paper-only. La validation `main` post-fusion est à contrôler séparément.
- Aucun changement de moteur, paramètres de robots, historiques, témoins Hold, interface ou secrets. Aucune nouvelle requête Gemini déclenchée : le bénéfice réel sur la qualité des réponses reste **à mesurer lors du prochain appel frais**, pas prouvé par la CI.

## 6. Infrastructure, limites et prochaines actions

- [Recherche #41439498444](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41439498444) : **SUCCESS**, étapes de tests et publication réussies ; [Paper #41452305805](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41452305805) : **SUCCESS** ; [Pages #41450924695](https://github.com/SeikoChillBot/AI-Trading/actions/runs/41450924695) : **SUCCESS**. `reports/system_health.json` du cycle 11:47 indiquait `research=running` pendant son exécution, alors que GitHub a ensuite confirmé `success` : snapshot temporel, pas une panne. L'ancien `research=unknown` du 01/11 n'est plus présent dans ce snapshot ; vérifier la fiabilité sur plusieurs cycles.
- L'accès au projet de facturation Gemini dans AI Studio et l'exécution réelle sur carnet de courtage ne sont pas disponibles via GitHub. Ne pas déduire un tarif de l'absence de `OPENAI_API_KEY`.
- Prochain contrôle : validation `main` post-fusion, premier nouvel appel Gemini non caché après PR #4, nombre et qualité des propositions structurées, qualité de l'étude des régimes, 90 journées prospectives et 10 trades avant toute promotion ; voie `shadow` à développer seulement avec tests ciblés de provenance/chronologie/idempotence.
