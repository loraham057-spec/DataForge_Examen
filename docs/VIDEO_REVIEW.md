# Revue de la vidéo fournie

## Constat technique

- Durée mesurée : **125,2 secondes**, soit environ **2 min 05 s**.
- Résolution : 1920×1080.
- La vidéo montre principalement l'interface Streamlit et la navigation entre les écrans.
- On voit le dashboard, les tableaux/graphiques et l'écran d'évaluation avec KoboToolbox.
- La vidéo ne couvre pas les 8 minutes d'explication du code exigées par le sujet.
- La démonstration ne montre pas de bout en bout un lancement Selenium complet, son avancement persistant, la fin du traitement et la synchronisation SQL.
- La vidéo ne montre pas clairement la distinction **RAW Web Scraper / CLEAN Selenium**, pourtant centrale dans le sujet.
- La vidéo ne montre pas la base SQL.
- L'écran montré dans la vidéo utilise l'ancienne identité `MY BEST DATA APP`, alors que le dépôt actuel contient `DATAFORGE` et plusieurs fonctions supplémentaires : il faut harmoniser le nom dans la nouvelle vidéo.

## Structure recommandée pour la nouvelle vidéo de 10 minutes

### 0:00–1:00 — Présentation

- objectif de l'examen ;
- deux sources ;
- distinction Selenium/CLEAN et Web Scraper/RAW ;
- architecture générale.

### 1:00–3:00 — Architecture du dépôt

Montrer :

- `app.py` ;
- `scraping/` ;
- `cleaning/` ;
- `data/raw/` ;
- `data/cleaned/` ;
- `data/database/` ;
- `scraper_runner.py`.

### 3:00–5:30 — Code Selenium

Expliquer :

- création du WebDriver ;
- navigation page par page ;
- extraction des variables ;
- pagination ;
- gestion des erreurs ;
- progression persistante ;
- spécificité Books et Gaaraas.

### 5:30–6:45 — Nettoyage et SQL

Montrer :

- `clean_books.py` ;
- `clean_gaaraas.py` ;
- types numériques ;
- valeurs manquantes ;
- dédoublonnage ;
- insertion dans les tables SQL.

### 6:45–8:00 — Application Streamlit

Expliquer les six écrans : présentation, scraping, RAW/CLEAN, dashboard, SQL, évaluation.

### 8:00–10:00 — Démonstration

1. choisir Books ;
2. lancer 1 page ;
3. montrer la progression ;
4. montrer le dataset CLEAN ;
5. montrer le dashboard ;
6. montrer RAW Web Scraper ;
7. montrer SQL ;
8. montrer Kobo + Google Forms.

## Message important

La vidéo actuelle n'est pas inutile : elle prouve que l'interface et le dashboard existent. Elle doit cependant être considérée comme une démonstration courte, pas comme le livrable final demandé par le sujet.
