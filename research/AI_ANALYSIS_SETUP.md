# Seiko Trading Lab — IA quotidienne sans facturation obligatoire
_Mise à jour : 28 octobre 2026. Recherche fictive uniquement._

## Ce qui est déjà automatique, sans aucune API IA
- GitHub Actions exécute quotidiennement le workflow `.github/workflows/research.yml` à 03:17 UTC, plus un lancement possible depuis l'onglet Actions.
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
4. Dans **Variables** (pas Secrets), créer `SEIKO_AI_ENABLED` avec la valeur `1` et `SEIKO_AI_PROVIDER` avec la valeur `gemini`.
5. Dans Actions, lancer manuellement **Seiko research — guarded automatic analysis → Run workflow**. Puis vérifier `reports/ai_research_status.json` et `reports/ai_research_proposals.json`.

Le code **fixe le modèle Gemini à `gemini-2.5-flash-lite`** dans l'appel. Il n'essaye aucun modèle plus cher et ne fait aucun repli vers OpenAI en cas de quota, clé invalide ou panne. Une seule tentative par journée UTC est conservée quand le workflow peut publier son rapport. Ce n'est pas une limite absolue contre des exécutions concurrentes GitHub. L'analyse statistique gratuite continue en cas de refus de l'API. Les changements de quota de Google peuvent empêcher la requête, sans rendre la recherche statistique payante.

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
