# Audit du projet — Data Collection

## Référence d'évaluation

L'audit est basé en premier lieu sur le document d'examen fourni avec le projet. Il exige :

1. scraping + nettoyage par **Selenium exclusivement** pour les deux sources ;
2. scraping RAW sans nettoyage avec **Web Scraper** ;
3. application Streamlit avec scraping multi-pages, téléchargement RAW, dashboard CLEAN et accès aux deux formulaires ;
4. base SQL ;
5. deux formulaires d'évaluation ;
6. livrables : application déployée, dépôt GitHub et vidéo de 10 minutes (8 min code + 2 min démonstration).

## Résultat de l'audit

| Exigence | État avant audit | Correction dans READY |
|---|---|---|
| Selenium pour le coding | Présent | Conservé et centralisé |
| BeautifulSoup interdit | Aucun import détecté | Aucun ajout |
| Books 50 pages | Scraper prévu pour 50 | Interface et runner 1–50 |
| Books variables | Incohérence entre `books_full` (20 lignes) et `books_clean` (1000) | `books_clean.csv` devient le dataset canonique |
| `products_count` Books | Absent du résultat final du scraper principal | Ajouté au contrat final |
| Nettoyage Books | Script existant mais non intégré au workflow Streamlit | Runner : Selenium → cleaning → SQL |
| Gaaraas 100 pages | Le site observé expose actuellement environ 13 pages | Interface 1–100 + pages vides tolérées |
| Gaaraas variables | Dataset CLEAN cohérent à 245 lignes | Conservé + parser renforcé |
| RAW no-code | Présent | Téléchargement explicite et séparé du CLEAN |
| Dashboard | Présent | Utilise désormais uniquement les CLEAN canoniques |
| SQL | Présent mais ancien état incohérent | Base reconstruite à 1000 Books + 245 Gaaraas |
| Persistance du scraping | Ancienne interface exécutait un subprocess bloquant | `scraper_runner.py` indépendant + état JSON |
| Progression | Partiellement présente dans les scrapers | Affichage Streamlit depuis l'état persistant |
| Évaluation | Liens présents | Écran dédié avec les deux liens |
| Vidéo | 2 min 05 s | À refaire selon la structure 8 min code + 2 min démo |

## Point critique de cohérence des données

Le projet contenait plusieurs générations de fichiers :

- `books_clean.csv` : 1 000 lignes ;
- `books_full.csv` : 20 lignes ;
- `books_full_completed.csv` : 20 lignes ;
- ancienne base SQL Books : 380 lignes ;
- `gaaraas_clean.csv` : 245 lignes ;
- `gaaraas_full.csv` : 235 lignes ;
- RAW Gaaraas Web Scraper : 237 lignes.

Cette coexistence rendait le choix de `latest()` dangereux : un fichier de test récent pouvait remplacer le dataset complet dans le dashboard. READY utilise maintenant deux fichiers CLEAN canoniques fixes.

## Limite documentaire

Le PDF précise que les questions, sections et logiques conditionnelles des formulaires sont détaillées dans un document de spécification séparé. Ce document n'était pas fourni dans les pièces auditées ; l'audit ne prétend donc pas vérifier le contenu exact des questions. Seule l'accessibilité des deux liens dans l'application est couverte.
