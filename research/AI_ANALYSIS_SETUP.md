# Seiko Trading Lab — IA quotidienne sans facturation obligatoire
_Mise à jour : 28 octobre 2026. Recherche fictive uniquement._

## Ce qui est déjà automatique, sans aucune API IA
- GitHub Actions planifie `.github/workflows/research.yml` toutes les deux heures à :17 UTC, avec déclenchement manuel et mécanisme de récupération si le cron est manqué. Les départs GitHub peuvent être retardés.
- Sources de données : Kraken OHLC, DeFiLlama, Alternative.me ; wallets uniquement si une liste vérifiée et une clé Etherscan sont configurées.
- Backtests historiques BTC / ETH / SOL, contrôles de sensibilité aux frais, comparaisons Hold, évaluation des risques et hypothèses déterministes.
- Rapports publiés dans `reports/`, exploités par l'onglet **Analyse** du site.
- Aucune modification des robots existants, aucun passage en argent réel.

## Activer une véritable IA gratuitement via Gemini
L'API Gemini propose un niveau sans frais pour certains modèles et projets, sous quotas. Les modèles, les restrictions et l'éligibilité du projet peuvent évoluer ; vérifier les pages officielles :
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/billing
- https://ai.google.dev/gemini-api/docs/troubleshooting

1. Créer / sélectionner dans https://aistudio.google.com/apikey un **projet Gemini de niveau gratuit**, sans compte de facturation associé. Vérifier l'éligibilité effective dans AI Studio (certains projets ne sont pas éligibles, même en France).
2. Créer une clé API sur le projet de niveau gratuit. Ne pas la coller dans les chats, fichiers, commits, issues ou autres pages publiques.
3. Sur GitHub : `SeikoChillBot/AI-Trading` → **Settings → Secrets and variables → Actions → Secrets → New repository secret**. Nom : `GEMINI_API_KEY`, valeur : la clé.
4. Le workflow utilise `SEIKO_AI_ENABLED=1` par défaut et **verrouille `SEIKO_AI_PROVIDER=gemini`** : une variable GitHub ne peut pas basculer ce workflow sur l'API OpenAI. Le secret Gemini suffit donc. Pour désactiver manuellement l'IA, créer `SEIKO_AI_ENABLED=0` dans Variables.
5. La première exécution après activation (run `40780569714`) a réussi : `model_reflection_completed`, clé API disponible, fournisseur Gemini. L'analyse quotidienne est planifiée, et le workflow reconstruit le tableau de bord après la recherche. Vérifier `reports/ai_research_status.json` et `reports/ai_research_proposals.json`.

Le code **fixe le modèle Gemini à `gemini-3.5-flash-lite`**, compatible avec les nouveaux projets. L'ancien Gemini 2.5 est désormais limité pour les nouvelles inscriptions. Il n'essaye aucun modèle plus cher et ne fait aucun repli vers OpenAI en cas de quota, clé invalide ou panne. Le workflow GitHub ne reçoit plus de variable `OPENAI_API_KEY` ni de sélection de modèle OpenAI. Les réponses Gemini sont mises en cache par créneau UTC de six heures, avec au plus une nouvelle tentative différée pour certains échecs transitoires ; ce n'est pas une limite absolue contre des exécutions concurrentes GitHub. L'analyse statistique gratuite continue en cas de refus de l'API. Les changements de quota de Google peuvent empêcher la requête, sans rendre la recherche statistique payante.

**Attention aux frais :** si une clé Gemini appartient à un projet de niveau payant, la requête peut être facturée malgré le choix de ce modèle. Le script ne peut pas vérifier la facturation du projet depuis la clé. Pour garantir l'absence de frais API, **utiliser exclusivement une clé d'un projet effectivement au niveau gratuit, sans facturation active**. Ne pas activer un palier payant pour surmonter un refus ou un quota.

**Données transmises :** seules des statistiques agrégées, des indicateurs de recherche et des hypothèses dépourvus de secrets, d'adresses de wallets et d'ordres détaillés. Dans le niveau gratuit, Google peut utiliser les données soumises pour améliorer ses produits : ne pas y transmettre d'informations sensibles ni des stratégies privées confidentielles.

## États du système
- `not_configured` : recherches et hypothèses déterministes ; aucun appel IA extérieure.
- `model_reflection_completed` et `source=gemini_generate_content` : l'IA Gemini a proposé des expériences **non validées**.
- `model_reflection_failed` : erreur/quota/format, remplacement par les suggestions déterministes.
- `historical_evidence_unavailable` : aucune requête au modèle faute d'historique suffisamment récent.

## Règles de recherche et coûts
- Un maximum de trois idées structurées par jour, sans modification des paramètres des 36 robots.
- Un historique déjà inspecté plusieurs fois ne peut pas servir indéfiniment de test « indépendant ».
- Pour évaluer une nouvelle stratégie, collecter des périodes inédites, comptabiliser les frais et le drawdown, comparer à la conservation passive, conserver les versions rejetées.
- Les abonnements ChatGPT/Google de chat ne sont pas des crédits API et n'améliorent pas la validité statistique.
- L'exécution GitHub Actions sur dépôt public est habituellement gratuite avec les runners hébergés standards, dans le respect des règles GitHub. Ne pas supposer que des runners haut de gamme ou tous les autres services sont gratuits.

Aucun mécanisme de simulation n'a accès à des clés de trading réel. L'existence d'un rapport IA ne prouve ni une meilleure prévision, ni une rentabilité future.

## Boucle autonome étendue — 28 octobre 2026 (23:40–23:45 heure de Paris)
- **Collecte et étude gratuite toutes les deux heures** : GitHub Actions cron `17 */2 * * *` UTC. Attention : GitHub peut décaler/sauter certains départs planifiés ; ce n'est pas un service de surveillance en temps réel.
- **Analyse Gemini au maximum quatre fois par jour**, soit une fois par créneau UTC de six heures, grâce au cache persistant `review_slot` et `model_last_called_at`. Les autres cycles actualisent les observations sans nouvelle requête IA.
- **Analyse de marché `reports/market_pulse.json`** : cours Kraken journaliers clôturés BTC/ETH/SOL, évolutions 1j/7j/30j, volatilité réalisée annualisée 30j, Fear & Greed, TVL Ethereum/Solana, émission de stablecoins (non assimilée à la demande future).
- **Transferts publics `research/large_transfers.py`** : échantillonnage limité des dernières 50 transactions pour USDC et USDT sur Ethereum via Blockscout, sans autre API payante. Contrats exacts vérifiés, taille nominale d'au moins 1 M USD pour les observations marquantes, premières observations utilisées uniquement comme point de référence, doublons évités avec `state/large_transfer_cursor.json`. Ce n'est **ni** une couverture exhaustive du réseau **ni** un suivi d'identités vérifiées. Un transfert ne prouve ni un achat, ni une vente ; aucun signal de trading n'en est déduit.
- **Incubateur prospectif `research/challenger_incubator.py`** : un challenger par BTC, ETH, SOL, chacun sur 20 USD fictifs. Paramètres figés au départ issus exclusivement de la grille statistique contrôlée du walk-forward ; **Gemini ne peut pas injecter de code ou d'ordres**. Enregistrement à la création : zéro transaction, zéro historique simulé rétroactivement. Ensuite, uniquement les nouveaux jours clôturés, avec frais hypothétiques et comparaison au Hold. En cas de trou de données, retraite et nouvelle version séparée ; ne pas fabriquer un parcours historique. L'incubateur ne modifie jamais les 36 robots de référence.
- L'onglet **Analyse** LAB/04 montre le marché, les gros transferts observés et le score prospectif des challengers. La collecte et les rapports sont publiés automatiquement après les tests de sécurité. Tous les résultats demeurent de la **recherche**, non des performances réelles.
- **Limite restante :** les expériences libres rédigées par Gemini sont encore des propositions **en langage naturel**. Les challengers autonomes proviennent actuellement de la grille de paramètres préapprouvée et non d'une génération arbitraire de code par IA. Cela sécurise le système, mais ne signifie pas que chaque idée Gemini est déjà testée automatiquement.
