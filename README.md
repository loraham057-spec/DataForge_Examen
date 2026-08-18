# DataForge

Application Streamlit de collecte, scraping, nettoyage, stockage SQLite,
visualisation et téléchargement de données.

## Sources prises en charge

- Books to Scrape
- Gaaraas

## Architecture

```text
DataForge
├── app/
│   └── streamlit_app.py
├── scraping/
│   ├── books_scraper.py
│   └── gaaraas_full_scraper.py
├── data/
│   ├── raw/
│   ├── cleaned/
│   ├── database/
│   └── temp/
├── scraper_runner.py
├── normalize_gaaraas.py
├── sync_sqlite_final.py
├── check_sqlite.py
├── check_csv.py
├── requirements.txt
├── .gitignore
└── Lancer_DataForge_Chrome.bat
```

## Pré-requis

- Windows
- Python 3.12
- Google Chrome
- connexion Internet
- environnement virtuel `venv312`

## Installation

Depuis la racine du projet :

```powershell
py -3.12 -m venv venv312
.env312\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Vérification :

```powershell
python --version
python -c "import streamlit,pandas,requests,bs4,selenium,openpyxl; print('DATAFORGE ENV OK')"
```

## Lancement

### Méthode recommandée

Double-cliquer sur :

```text
Lancer_DataForge_Chrome.bat
```

Le script démarre Streamlit avec `venv312` puis ouvre :

```text
http://localhost:8501
```

dans Google Chrome.

### Méthode PowerShell

```powershell
.env312\Scripts\Activate.ps1
python -m streamlit run ".pp\streamlit_app.py"
```

## Tests rapides

### Books

```powershell
python ".\scrapingooks_scraper.py"
```

### Gaaraas

```powershell
python ".\scraping\gaaraas_full_scraper.py" 1 1
```

### Vérifier les CSV

```powershell
python ".\check_csv.py"
```

### Vérifier SQLite

```powershell
python ".\check_sqlite.py"
```

### Synchroniser SQLite

Après validation des CSV :

```powershell
python ".\sync_sqlite_final.py"
```

## Fonctionnement du scraping

Le nombre de pages demandé doit être respecté par le runner.

Le scraping est exécuté indépendamment de l'interface Streamlit afin que la navigation entre les pages de l'application n'interrompe pas la collecte.

Les états temporaires sont stockés dans :

```text
data/temp/
```

Les résultats nettoyés sont stockés dans :

```text
data/cleaned/
```

La base SQLite est stockée dans :

```text
data/database/
```

## Données Gaaraas

Les annonces sont identifiées par `listing_url`.

Lorsque le site renvoie un titre générique comme `Notre histoire`, le traitement de normalisation utilise le slug de `listing_url` pour reconstruire la marque et le modèle lorsque cela est possible.

## Validation avant livraison

Avant une livraison :

1. tester Books sur 1 page ;
2. tester Books sur plusieurs pages ;
3. tester Gaaraas sur 1 page ;
4. vérifier les URLs uniques et les doublons ;
5. synchroniser SQLite ;
6. vérifier les compteurs SQLite ;
7. tester les téléchargements CSV/Excel ;
8. tester le Dashboard ;
9. tester la navigation pendant un scraping ;
10. tester le lancement via Chrome.

## Déploiement

### Déploiement local Windows

Copier le dossier complet sur la machine cible, installer Python 3.12,
créer `venv312`, installer `requirements.txt`, puis utiliser
`Lancer_DataForge_Chrome.bat`.

### Important

Ne pas versionner :

- `venv/`
- `venv312/`
- les bases SQLite générées
- les CSV générés
- les fichiers temporaires
- les données brutes potentiellement volumineuses

Le `.gitignore` fourni est prévu pour cela.

## Dépannage

### Python introuvable

```powershell
py -0p
```

### Vérifier Python 3.12

```powershell
.env312\Scripts\python.exe --version
```

### Streamlit

```powershell
.env312\Scripts\python.exe -m streamlit run ".pp\streamlit_app.py"
```

### Selenium

```powershell
.env312\Scripts\python.exe -c "import selenium; print(selenium.__version__)"
```

## État du projet

DataForge est conçu pour fournir une chaîne complète :

```text
Source Web
   ↓
Scraping
   ↓
Progression
   ↓
CSV
   ↓
Nettoyage
   ↓
SQLite
   ↓
Dashboard
   ↓
CSV / Excel
```
