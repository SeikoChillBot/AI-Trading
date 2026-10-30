# Seiko Trading Lab — Recherche automatique

Date UTC : 2026-10-30T18:45:47.941936+00:00

**État : analyse statistique automatique. La disponibilité de l’IA générative est indiquée séparément.**
**Aucune stratégie modifiée ni aucun ordre réel.**

## Données observées
- **crypto** : 18 robots, 2.011 jour(s) de données, 360.00 $ fictifs de référence, 22.1280 $ de frais déjà enregistrés, **0 éligibles à une revue**.
- **multi** : 18 robots, 1.915 jour(s) de données, 360.00 $ fictifs de référence, 0.2497 $ de frais déjà enregistrés, **0 éligibles à une revue**.

**Conclusion : 0 stratégie(s) suffisamment documentée(s) pour une revue ; aucune rentabilité démontrée.**

## Hypothèses proposées (non testées)

### WAIT-000 — Priorité : observer sans modifier les stratégies
- Pourquoi : Aucune des deux cohortes ne possède encore assez de transactions clôturées et de recul temporel.
- Expérience : Accumuler des observations horodatées et vérifier que les données ne sont pas manquantes ou recalculées rétroactivement.
- Condition de validation : Garder les 36 robots de référence inchangés et préparer des challengers indépendants.
- Statut : active_research_gate

### COST-STRESS-001 — Éprouver la sensibilité des robots courts aux frais
- Pourquoi : Avec des mises de 20 $, le coût aller-retour peut dominer le signal.
- Expérience : Rejouer exactement les mêmes signaux avec frais actuels, +50 % et +100 %, en période hors échantillon.
- Condition de validation : Comparer rendement net, drawdown et nombre de positions ; ne pas promouvoir une variante sur le seul gain brut.
- Statut : hypothesis_only_no_test

### THRESHOLD-002 — Étudier des seuils d'entrée plus sélectifs
- Pourquoi : Un seuil plus exigeant peut réduire la rotation et les frais, mais aussi manquer des tendances.
- Expérience : Comparer à règles fixes les seuils actuels, plus stricts et moins stricts sur plusieurs fenêtres chronologiques disjointes.
- Condition de validation : Conserver un témoin inchangé, pénaliser la complexité et regarder le rendement net hors échantillon.
- Statut : hypothesis_only_no_test

### SMA-003 — Comparer SMA10, SMA20 et SMA40 en actions / ETF
- Pourquoi : La bonne fréquence dépend des coûts et de l'actif ; aucune période optimale n'est connue aujourd'hui.
- Expérience : Backtests chronologiques par marché, dividendes et opérations sur titres correctement intégrés, puis paper trading prospectif.
- Condition de validation : Ne sélectionner aucune combinaison sans données de prix fiables et validation hors échantillon.
- Statut : blocked_until_data_quality_confirmed

### FRACTIONS-004 — Valider les ordres fractionnés de 20 $ chez un courtier réel
- Pourquoi : Les fractions d'ETF US et les minima de courtage ne sont pas vérifiés pour un compte en France.
- Expérience : Contrôler l'instrument, la permission du courtier, le minimum d'ordre, la commission et la disponibilité européenne.
- Condition de validation : N'afficher comme exécutable que ce qu'un courtier de référence accepte effectivement.
- Statut : blocked_until_broker_verified

### BASELINE-005 — Ajouter DCA, conservation et liquidités comme témoins
- Pourquoi : Une stratégie active doit battre un témoin réaliste après frais, pour un risque comparable.
- Expérience : Comparer les trajectoires aux mêmes dates et sur le même actif, sans utiliser les cours futurs.
- Condition de validation : Comparer rendement total net, temps investi et drawdown, sans fusionner les cohortes.
- Statut : hypothesis_only_no_test

## Limites et règles
- Aucune promesse de rentabilité, d'alpha ou de revenu mensuel.
- Les historiques restent intacts ; seuls des paramètres fictifs préautorisés peuvent évoluer après validation prospective indépendante.
- Aucun ordre réel, effet de levier ou connexion courtier.
- Une optimisation future doit être vérifiée hors échantillon (walk-forward).
- Les ETF US fractionnés et les taux BCE ne démontrent pas l'exécutabilité chez un courtier.

Le modèle génératif éventuel doit formuler des hypothèses, non voter une modification des robots actifs.
