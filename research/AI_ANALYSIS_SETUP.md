# Seiko Trading Lab — IA de recherche et optimisation contrôlée
_Mise à jour le 28 octobre 2026. Recherche fictive uniquement._

## Fonctionnement
- La recherche statistique fonctionne gratuitement, sans clé API.
- Les challengers historiques BTCUSD/ETHUSD/SOLUSD sont évalués sur des fenêtres walk-forward avec capital fictif de 20 USD, coûts de transaction et stress sur les frais.
- research/ai_decision_support.py produit des indicateurs de robustesse : rendement moyen net, comparaison Hold, transactions clôturées, frais doublés, drawdown.
- research/ai_reflection.py publie reports/ai_research_proposals.json, reports/ai_research.md et reports/ai_research_status.json.
- Sans modèle connecté, les idées sont déterministes et identifiées comme telles ; l'onglet Analyse LAB/04 affiche ces observations et leurs limites.
- Aucun ordre réel, aucun paramètre ou portefeuille actif ne peut être modifié par ce module.

## Connexion facultative à l'API d'IA
1. Disposer d'un compte API OpenAI avec un budget configuré (abonnement ChatGPT distinct des crédits API).
2. Dans le dépôt SeikoChillBot/AI-Trading, Settings → Secrets and variables → Actions, créer le secret OPENAI_API_KEY. Ne pas conserver de clé en clair dans Git.
3. Dans Variables, ajouter SEIKO_AI_MODEL avec un modèle compatible Responses API et sortie JSON Schema stricte (par exemple gpt-6-luna si accessible).
4. Ajouter SEIKO_AI_ENABLED = 1. Tant qu'une clé, un modèle ou l'activation manque, aucun appel payant.
5. Pour un essai manuel : Actions → Seiko research — guarded automatic analysis → Run workflow. Exécution automatique quotidienne programmée à 03:17 UTC.
6. Vérifier reports/ai_research_status.json. model_reflection_completed indique qu'une réponse du modèle a été obtenue ; not_configured signifie une analyse déterministe ; model_reflection_failed signifie échec avec repli statistique.

Les réponses du modèle sont structurées et validées, limitées à trois propositions sur BTC/ETH/SOL. Aucun accès du modèle aux outils d'ordres ni aux secrets. Une tentative réussie ou échouée est mémorisée par journée UTC si le workflow a pu publier ses rapports, réduisant les appels répétés. Ce n'est pas un plafond de facturation garanti : définir aussi une limite de dépenses sur la plateforme API.

## Validation avant toute modification
- L'IA propose des hypothèses, elle ne choisit pas automatiquement les investissements.
- Évaluer les pistes sur des données chronologiquement nouvelles, jamais utilisées pour sélectionner les paramètres : les fenêtres historiques déjà explorées ne deviennent pas « inédites ».
- Préserver les témoins Hold et liquidités, la qualité des sources, la taille de 20 USD, les coûts et minima d'ordre.
- Exiger une résistance à des frais accrus, un nombre suffisant de transactions, une réduction des risques et une simulation prospective indépendante.
- Conserver les 36 robots et leurs historiques ; créer d'éventuels challengers dans des cohortes distinctes.
- Une IA conversationnelle n'est pas une preuve de capacité à prévoir les marchés ou à générer des bénéfices futurs.
