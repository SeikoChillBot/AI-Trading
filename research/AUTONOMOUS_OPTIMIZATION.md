# Seiko Lab — boucle de recherche automatique

## En service
GitHub Actions lance quotidiennement research/auto_research.py.
Le programme lit les rapports de 36 robots fictifs à 20 USD, contrôle la qualité des données et propose des hypothèses non testées.

Rapports : reports/autonomous_research.json, reports/autonomous_research.md, reports/autonomous_research_history.jsonl.

## IA optionnelle
research/ai_reflection.py est désactivé par défaut et ne coûte rien sans activation.
Pour utiliser un modèle d'IA, configurer dans GitHub Settings > Secrets and variables > Actions :
- secret OPENAI_API_KEY
- variable SEIKO_AI_ENABLED = 1
- variable SEIKO_AI_MODEL = identifiant du modèle API choisi

L'API est facturée séparément de ChatGPT. Ne jamais mettre sa clé dans le code ou le chat.
L'IA ne reçoit que des métriques de recherche, ne possède aucun outil de trading et ne modifie pas les stratégies. Les réponses sont des idées et non des performances validées.

## Étapes à développer
1. Historique de cotations vérifiables sur plusieurs régimes de marché.
2. Backtest de variantes avec spreads, frais et ordres réalistes.
3. Validation chronologique hors échantillon et comparaison aux témoins.
4. Challengers fictifs de 20 USD séparés ; aucun changement rétroactif.
5. Revue humaine avant remplacement d'un robot principal.

La simulation actuelle ne suffit pas encore à désigner une stratégie rentable.
