# AIT — boucle autonome, transparence et limites (29 octobre 2026)

## Automatisation active
- 36 robots de référence en simulation fictive ; 12 Hold sont des témoins non modifiables.
- Collecte Paper trading planifiée toutes les cinq minutes ; recherche de marché toutes les deux heures, sous réserve des retards ou quotas de GitHub Actions.
- Gemini 3.5 Flash-Lite en niveau gratuit sous réserve de l'éligibilité du projet et de ses quotas : maximum 4 créneaux d'analyse par jour. Lors d'un refus API, le moteur statistique continue sans basculer vers un modèle payant. Le journal `reports/ai_research_status.json` doit être consulté pour distinguer le modèle de son repli statistique.
- 24 robots ajustables : inscription progressive de 4 comparaisons prospectives par recherche jusqu'à couverture complète des 24, chaque variante avec son témoin, frais et double frais. Adoption en simulation seulement si validation hors échantillon et respect du risque ; retour arrière automatique prévu.
- Expériences fictives de placement spot, 20 USD par scénario, sans demande d'approbation : jusqu'à 4 nouvelles inscriptions par cycle et 12 simultanées ; plusieurs horizons 1/3/7 jours BTC/ETH/SOL. Sans nouveauté Gemini, recherches statistiques autonomes. Déduplication des relances GitHub sur chaque créneau de 2 heures. Les scénarios restent distincts des 36 robots de référence.
- Études Kraken 60 minutes BTC, ETH et SOL : fenêtres d'entraînement et tests chronologiques séparées ; suivi prospectif fictif indépendant, frais modélisés et drawdown. Ce n'est pas un flux de trading haute fréquence ni une exécution au carnet d'ordres.
- Échantillonnage des transferts USDC/USDT Ethereum via Blockscout : jusqu'à 3 pages de 50 lignes par contrat et par cycle ; validation des contrats, montants, horodatages et hashes ; aucune inférence de propriétaire, d'achat ou de vente.
- Actualités sourcées (Fed, BCE, CoinDesk), notes Gemini et patchnotes correspondant aux changements réellement enregistrés.

## Interface de suivi
- **Analyse → État réel du laboratoire** : feuille de route alimentée par les rapports et statut de fiabilité.
- **Analyse → Études horaires** : résultats hors échantillon après frais et suivis fictifs prospectifs.
- **Analyse → Évolution des robots** : 36 fiches individuelles, propositions et journaux.
- **Journal IA** : notes, expériences, actualités, radar et patchnotes.

## Contrôles automatiques
- `research/ops_status.py` contrôle fraîcheur des données et dernières exécutions terminées GitHub. Un échec plus ancien qu'une réussite n'est pas une panne courante. Les alertes sont publiées dans `reports/system_health.json`; cela **ne désactive pas** les e-mails natifs GitHub.
- `research/ai_reflection.py` conserve le statut de l'appel API. Si Google refuse le grand schéma JSON avec HTTP 400, le même fournisseur peut être sollicité une seule fois avec un schéma plus léger. Aucun retry automatique sur HTTP 429 (quota), et aucune bascule payante.
- La validation GitHub et les tests existants précèdent les mises à jour des données ; une erreur de vue ne doit pas arrêter la sauvegarde des portefeuilles.

## Ce qui ne peut pas être considéré comme démontré ou complet
- Aucun résultat de rentabilité future garanti, aucun bénéfice réel, aucun courtier ou portefeuille connecté à l'argent réel.
- Suivi des baleines : échantillonnage on-chain plus large **mais non exhaustif** et **sans attribution fiable des identités / positions de trading**. Une véritable attribution nécessitera des données vérifiées supplémentaires, avec leurs limites ou coûts.
- Optimisation des 24 robots : tests d'hypothèses de paramètres bornés ; le modèle ne peut toujours pas réécrire et exécuter librement tous les algorithmes Python. Des périodes prospectives, suffisamment de trades et des benchmarks sont indispensables pour adopter une variante.
- Surveillance GitHub : Actions n'offre pas de garantie de démarrage à la minute et les e-mails des anciens runs restent visibles même après réparation.
- Gemini : la première analyse du créneau 2026-10-29T00:00Z a rencontré une erreur HTTP ; au moment de ce document, le système était en repli statistique. Une réexécution future réussie est nécessaire pour confirmer la réparation API.

## AIT / 05 — reprise fiabilité, portefeuilles et radar (29 octobre 2026)

- Fiches des 36 stratégies : capital fictif de départ, cash disponible, unités détenues et position. Données issues de `reports/realistic_latest.csv` / `reports/multi_asset_micro_latest.csv`, jamais recalculées avec une transaction inventée. Courbes de capital par robot et filtres 24h / 7j / Tout, repères horodatés et indicateur de fraîcheur de la publication. Les cinq onglets du bas sont inchangés ; aucune modification de navigation Android.
- Recherche Gemini : erreurs HTTP, catégories de réponse invalide, dates et essais par créneau journalisés sans texte de réponse sensible. Une tentative provisoirement échouée peut être rejouée après 90 minutes **au plus une seconde fois dans le créneau de 6 heures**, sauf 401/403/404/429. Pas de bascule payante ; un workflow réussi ne prouve pas que Gemini a répondu. Le seul statut `model_reflection_completed` après réponse validée confirme la génération.
- Transferts USDC/USDT Ethereum via Blockscout : 3 pages maximum par token dans la première couche. Nouveaux `sampled_wallet_flows` et `sample_highlights` ; mouvement directionnel **dans l'échantillon seulement**, jamais solde de compte ni signe d'achat. Nouvelle deuxième couche `research/whale_follow.py` : suit au plus 4 adresses pseudonymes sélectionnées depuis l'échantillon via la page publique de transferts ERC-20 par adresse, garde un état et n'annonce aucun événement « nouveau » au premier relevé. Pas d'attribution propriétaire ni de couverture exhaustive ; aucune clé privée.
- Rapports nouveaux/étendus : `reports/large_transfer_observations.json`, `reports/whale_follow.json`, `state/whale_follow_state.json`. Publication vers `DATA.whale_radar` dans `build_site.py`, cartes lisibles dans l'onglet Analyse avec liens de transactions et d'adresses.
- Rapport GitHub Pages : nouveau badge indiquant la date des derniers relevés crypto et multi, conservateur si l'un manque ou dépasse le seuil de fraîcheur. Une page statique n'est pas un flux direct.
- Workflow `research.yml` intégré et tests de régression `tests/test_ait_upgrade.py` inclus. La preuve de déploiement effectif et le premier résultat Google sous le nouveau code doivent être vérifiés sur les prochains runs ; **ne jamais confondre un commit de code avec un run publié et réussi**.
- Préférence utilisateur : notifications e-mail GitHub déjà résolues, **ne pas reconfigurer**. Barre de navigation flottante validée, **ne pas modifier**. Tous les ordres restent fictifs.
