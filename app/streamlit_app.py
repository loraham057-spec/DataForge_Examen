# ============================================================
# DATAFORGE — VERSION STRICT PROJECT
# ============================================================
# Objectif :
#   Application Streamlit dédiée au projet de Data Collection.
#
# Périmètre conservé :
#   1. Scraping Selenium — Books to Scrape
#   2. Scraping Selenium — Gaaraas
#   3. Téléchargement des données collectées
#   4. Visualisation / Dashboard
#   5. Base SQL SQLite
#   6. Évaluation : KoboToolbox + Google Forms
#
# Aucun ajout fonctionnel hors périmètre :
#   - pas de thème personnalisé
#   - pas de changement de langue
#   - pas de localisation configurable
#   - pas de mode jour/nuit
#   - pas d'animation
#   - pas de fonctionnalités métier supplémentaires
#
# Les commentaires décrivent le rôle de chaque partie pour faciliter
# l'explication du code pendant la présentation.
# ============================================================

import os
import sys
import subprocess
import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# ============================================================
# 1. CHEMINS DU PROJET
# Description : définit les dossiers utilisés par les scripts
# Selenium et les fichiers CSV nettoyés.
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
SCRAPING = ROOT / "scraping"
CLEANED = ROOT / "data" / "cleaned"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# ============================================================
# 2. BASE DE DONNÉES SQL
# Description : utilise la couche SQLite déjà présente dans
# app/data_database.py. Aucune nouvelle architecture SQL n'est
# créée ici.
# ============================================================

from data_database import (
    init_database,
    sync_dataset,
    read_table,
    table_count,
    list_tables,
    database_path,
)

init_database(ROOT)

# ============================================================
# 3. SCRIPTS SELENIUM
# Description : références vers les scripts existants du projet.
# ============================================================

BOOKS = SCRAPING / "books_scraper.py"
GAARAAS = SCRAPING / "gaaraas_full_scraper.py"
RUNNER = ROOT / "scraper_runner.py"
JOB_STATE = ROOT / "data" / "temp" / "dataforge_scraping_job.json"

# ============================================================
# 4. DATASETS
# Description : fichiers produits par les scrapers.
# ============================================================

BOOK_FILES = [
    CLEANED / "books_full.csv",
    CLEANED / "books_clean.csv",
]

GAARAAS_FILES = [
    CLEANED / "gaaraas_full.csv",
    CLEANED / "gaaraas_clean.csv",
]


# ============================================================
# 5. PARAMÈTRES D'INTERFACE
# Description : thème, luminosité, langue, localisation et
# liens des formulaires. Ces paramètres ne modifient pas le
# fonctionnement des scrapers ni de la base de données.
# ============================================================

THEMES = {
    "🧊 Arctic": {
        "day_bg": "#EEF7FB", "day_card": "#FFFFFF", "day_accent": "#1976A3",
        "night_bg": "#0B1220", "night_card": "#111C2E", "night_accent": "#4DB6E5",
    },
    "🌊 Ocean": {
        "day_bg": "#EAF7FA", "day_card": "#FFFFFF", "day_accent": "#087F8C",
        "night_bg": "#08181C", "night_card": "#10272C", "night_accent": "#43C6D3",
    },
    "🌿 Emerald": {
        "day_bg": "#F1F8F4", "day_card": "#FFFFFF", "day_accent": "#18794E",
        "night_bg": "#0B1711", "night_card": "#12231A", "night_accent": "#54C58A",
    },
    "🌌 Cosmic": {
        "day_bg": "#F4F2FC", "day_card": "#FFFFFF", "day_accent": "#6842B8",
        "night_bg": "#100D1C", "night_card": "#1A162B", "night_accent": "#A98AE8",
    },
    "🪨 Slate": {
        "day_bg": "#F1F4F7", "day_card": "#FFFFFF", "day_accent": "#475569",
        "night_bg": "#111827", "night_card": "#1B2638", "night_accent": "#94A3B8",
    },
}

LANGUAGES = {
    "🇫🇷 Français": {
        "subtitle": "Collecte, téléchargement et visualisation des données web.",
        "source": "Source de données",
        "pages": "Pages à traiter",
        "function": "Fonctionnalité",
    },
    "🇬🇧 English": {
        "subtitle": "Collect, download and visualize web data.",
        "source": "Data source",
        "pages": "Pages to process",
        "function": "Function",
    },
}

LOCATIONS = [
    "Kinshasa, RDC",
    "Lubumbashi, RDC",
    "Kisangani, RDC",
    "Dakar, Sénégal",
    "Autre",
]

KOBO_DEFAULT = "https://ee.kobotoolbox.org/x/1oNIZ8OJ"
GOOGLE_DEFAULT = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLScFmWJm7vxf0UYLhoVVr1V4UBpOADke6rzt1CrV4rgnFE2Wmg/"
    "viewform?usp=header"
)

for _key, _value in {
    "df_theme": "🧊 Arctic",
    "df_language": "🇫🇷 Français",
    "df_location": "Kinshasa, RDC",
    "df_display": "🌙 Nuit",
    "df_kobo_url": KOBO_DEFAULT,
    "df_google_url": GOOGLE_DEFAULT,
    "df_settings_open": False,
}.items():
    if _key not in st.session_state:
        st.session_state[_key] = _value


# ============================================================
# 5. CONFIGURATION STREAMLIT
# Description : configuration minimale nécessaire à l'application.
# ============================================================

st.set_page_config(
    page_title="MY DATA COLLECTION APP DATAFORGE",
    page_icon="🕷️",
    layout="wide",
)

# ============================================================
# 6. DESIGN SIMPLE
# Description : amélioration visuelle légère sans fonctionnalité
# supplémentaire et sans animation.
# ============================================================

# ============================================================
# DESIGN / CSS
# Description : calcule les couleurs puis injecte un CSS.
# Le CSS reste une chaîne Python normale : les accolades CSS
# ne sont donc jamais interprétées comme des variables Python.
# ============================================================

_current_theme = THEMES[st.session_state.df_theme]
_is_night = st.session_state.df_display == "🌙 Nuit"

_css_bg = _current_theme["night_bg"] if _is_night else _current_theme["day_bg"]
_css_card = _current_theme["night_card"] if _is_night else _current_theme["day_card"]
_css_accent = _current_theme["night_accent"] if _is_night else _current_theme["day_accent"]
_css_text = "#F8FAFC" if _is_night else "#172033"
_css_muted = "#D0D8E2" if _is_night else "#64748B"
_css_border = "#334155" if _is_night else "#D7E0E8"

st.markdown(
    f"""
    <style>
    :root {{
        --df-bg: {_css_bg};
        --df-card: {_css_card};
        --df-accent: {_css_accent};
        --df-text: {_css_text};
        --df-muted: {_css_muted};
        --df-border: {_css_border};
    }}

    .stApp {{
        min-height: 100vh;
        background:
            radial-gradient(
                circle at 85% 8%,
                color-mix(in srgb, var(--df-accent) 16%, transparent),
                transparent 28%
            ),
            linear-gradient(
                135deg,
                var(--df-bg) 0%,
                color-mix(in srgb, var(--df-bg) 92%, var(--df-accent)) 100%
            );
        color: var(--df-text) !important;
    }}

    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    [data-testid="stMainBlockContainer"] {{
        background: transparent;
        border-radius: 24px;
        padding-top: 12px;
    }}

    /* Sidebar sombre et lisible */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg,
            rgba(7, 18, 34, 0.99),
            rgba(10, 30, 50, 0.99)
        ) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.18);
    }}

    section[data-testid="stSidebar"] > div {{
        background: transparent !important;
    }}

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
        color: #F8FAFC !important;
    }}

    /* Selectbox : fond blanc + texte sombre */
    section[data-testid="stSidebar"] [data-baseweb="select"] {{
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        min-height: 50px !important;
        box-shadow: none !important;
    }}

    section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background: #FFFFFF !important;
        border-radius: 12px !important;
        color: #172033 !important;
    }}

    section[data-testid="stSidebar"] [data-baseweb="select"] [role="button"],
    section[data-testid="stSidebar"] [data-baseweb="select"] [role="button"] *,
    section[data-testid="stSidebar"] [data-baseweb="select"] input {{
        color: #172033 !important;
        -webkit-text-fill-color: #172033 !important;
    }}

    section[data-testid="stSidebar"] [data-baseweb="select"] svg {{
        fill: #334155 !important;
        color: #334155 !important;
    }}

    [data-baseweb="popover"] {{
        z-index: 999999 !important;
    }}

    [data-baseweb="menu"] {{
        background: #FFFFFF !important;
        color: #172033 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
    }}

    [data-baseweb="menu"] *,
    [data-baseweb="menu"] [role="option"] {{
        color: #172033 !important;
        -webkit-text-fill-color: #172033 !important;
    }}

    [data-baseweb="menu"] [aria-selected="true"] {{
        background: #E8F2F8 !important;
        color: #0F4C68 !important;
    }}

    /* Champ Pages */
    section[data-testid="stSidebar"] input {{
        background: #FFFFFF !important;
        color: #172033 !important;
        -webkit-text-fill-color: #172033 !important;
        border-radius: 12px !important;
    }}

    /* Contenu */
    .df-title {{
        font-size: clamp(30px, 4vw, 46px);
        line-height: 1.05;
        font-weight: 850;
        letter-spacing: -1px;
        color: var(--df-text) !important;
        text-shadow: 0 2px 12px rgba(15, 23, 42, 0.10);
    }}

    .df-subtitle {{
        color: var(--df-muted) !important;
        font-size: 16px;
        margin-bottom: 10px;
    }}

    .df-line {{
        height: 4px;
        width: 115px;
        border-radius: 20px;
        background: linear-gradient(90deg, var(--df-accent), transparent);
        margin: 10px 0 24px;
    }}

    .df-card,
    .df-form-card {{
        background: var(--df-card);
        border: 1px solid var(--df-border);
        border-radius: 18px;
        box-shadow: 0 8px 26px rgba(15, 23, 42, 0.10);
    }}

    .df-form-card {{
        padding: 22px;
        text-align: center;
        min-height: 145px;
    }}

    .df-form-icon {{
        font-size: 36px;
    }}

    .df-form-title {{
        color: var(--df-text) !important;
        font-size: 22px;
        font-weight: 800;
        margin: 6px 0;
    }}

    .df-form-description {{
        color: var(--df-muted) !important;
        margin-bottom: 12px;
    }}

    [data-testid="stMetric"] {{
        background: var(--df-card);
        border: 1px solid var(--df-border);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 7px 22px rgba(15, 23, 42, 0.08);
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--df-muted) !important;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--df-text) !important;
    }}

    .stButton > button,
    .stLinkButton > a {{
        border-radius: 12px !important;
        min-height: 44px !important;
        font-weight: 750 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)





# ============================================================
# 7. BOUTON PARAMÈTRES
# Description : panneau en haut à droite permettant de changer
# le fond, Jour/Nuit, la langue, la localisation et les liens.
# ============================================================

_top_left, _top_right = st.columns([9, 1])

with _top_right:
    if st.button("⚙️", key="df_settings_button", help="Paramètres"):
        st.session_state.df_settings_open = not st.session_state.df_settings_open

if st.session_state.df_settings_open:
    st.markdown(
        '<div class="df-card" style="padding:18px;"><b>⚙️ Paramètres DATAFORGE</b></div>',
        unsafe_allow_html=True,
    )

    _s1, _s2, _s3, _s4 = st.columns(4)

    with _s1:
        _new_theme = st.selectbox(
            "🎨 Couleur / thème",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state.df_theme),
            key="df_theme_select",
        )

    with _s2:
        _new_language = st.selectbox(
            "🌐 Langue",
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.df_language),
            key="df_language_select",
        )

    with _s3:
        _new_location = st.selectbox(
            "📍 Localisation",
            LOCATIONS,
            index=LOCATIONS.index(st.session_state.df_location),
            key="df_location_select",
        )

    with _s4:
        _new_display = st.selectbox(
            "💡 Affichage",
            ["☀️ Jour", "🌙 Nuit"],
            index=["☀️ Jour", "🌙 Nuit"].index(st.session_state.df_display),
            key="df_display_select",
        )

    st.markdown("#### 🔗 Liens des formulaires")

    _kobo = st.text_input(
        "📝 KoboToolbox",
        value=st.session_state.df_kobo_url,
        key="df_kobo_input",
    )

    _google = st.text_input(
        "📋 Google Forms",
        value=st.session_state.df_google_url,
        key="df_google_input",
    )

    if st.button("💾 Enregistrer les paramètres", type="primary", key="df_save_settings"):
        st.session_state.df_theme = _new_theme
        st.session_state.df_language = _new_language
        st.session_state.df_location = _new_location
        st.session_state.df_display = _new_display
        st.session_state.df_kobo_url = _kobo.strip()
        st.session_state.df_google_url = _google.strip()
        st.rerun()

L = LANGUAGES[st.session_state.df_language]
CURRENT_SUBTITLE = L["subtitle"]

# ============================================================
# 7. OUTILS
# Description : fonctions génériques de lecture et recherche des
# fichiers les plus récents.
# ============================================================

def latest(files):
    """Retourne le fichier existant le plus récemment modifié."""
    existing = [f for f in files if f.exists()]
    return max(existing, key=lambda f: f.stat().st_mtime) if existing else None


def read_csv(path):
    """Lit un CSV et retourne un DataFrame."""
    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.error(f"Erreur de lecture du fichier : {exc}")
        return None


# ============================================================
# 8. EXÉCUTION SELENIUM
# Description : exécute un script de scraping et affiche ses logs.
# ============================================================

def _database_size(root):
    """Retourne la taille de la base SQLite en octets."""
    db = root / "data" / "database" / "data_collection.db"
    return db.stat().st_size if db.exists() else 0


def _read_job_state():
    """Lit l'état persistant du scraper sans dépendre de la page Streamlit."""
    if not JOB_STATE.exists():
        return None
    try:
        return json.loads(JOB_STATE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _start_scraping(dataset, pages):
    """Lance le scraper dans un processus indépendant de Streamlit."""
    if not RUNNER.exists():
        st.error(f"❌ Runner introuvable : {RUNNER}")
        return False

    state = _read_job_state() or {}
    if state.get("status") in {"starting", "running"}:
        st.warning("⏳ Un scraping est déjà en cours.")
        return False

    JOB_STATE.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        subprocess.Popen(
            [sys.executable, str(RUNNER), dataset, str(int(pages)), str(ROOT)],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        return True
    except Exception as exc:
        st.error(f"❌ Impossible de démarrer le scraping : {exc}")
        return False


def _show_scraping_progress():
    """Affiche l'état du job. Le processus continue même si l'utilisateur navigue."""
    state = _read_job_state()
    if not state:
        return

    status = state.get("status", "unknown")
    current = int(state.get("current_page", 0) or 0)
    total = int(state.get("total_pages", state.get("pages", 1)) or 1)
    total = max(total, 1)
    progress = min(max(current / total, 0.0), 1.0)
    dataset = state.get("dataset", "").upper()
    message = state.get("message", "")

    if status in {"starting", "running"}:
        st.info(f"🔄 Scraping {dataset} en cours — {message}")
        st.progress(progress, text=f"Page {current}/{total} — {progress:.0%}")
        st.caption("Vous pouvez changer de page dans DataForge : le scraping continue en arrière-plan.")
    elif status == "completed":
        st.success(f"✅ Scraping {dataset} terminé — {message}")
        st.progress(1.0, text=f"Terminé — {total}/{total} pages")

        # Synchronisation SQLite une seule fois après la fin du job.
        if not state.get("sql_synced"):
            output_value = state.get("output")
            if output_value:
                output_path = Path(output_value)
                if output_path.exists():
                    try:
                        count = sync_dataset(ROOT, dataset.lower(), output_path)
                        # Le fichier d'état est réécrit pour éviter une synchronisation répétée.
                        state["sql_synced"] = True
                        state["sql_rows"] = count
                        JOB_STATE.write_text(
                            json.dumps(state, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        st.success(f"🗄️ SQLite synchronisée : {count:,} lignes.")
                    except Exception as exc:
                        st.warning(f"⚠️ CSV disponible mais synchronisation SQLite impossible : {exc}")

        # Aperçu immédiat du résultat final.
        output_value = state.get("output")
        if output_value and Path(output_value).exists():
            try:
                result_df = pd.read_csv(output_value)
                st.caption(f"🕷️ Résultat : {len(result_df):,} lignes")
                st.dataframe(result_df.head(20), use_container_width=True, hide_index=True)
                c1, c2 = st.columns(2)
                csv_bytes = result_df.to_csv(index=False).encode("utf-8-sig")
                with c1:
                    st.download_button(
                        "⬇️ Télécharger CSV", csv_bytes,
                        file_name=Path(output_value).name,
                        mime="text/csv",
                        use_container_width=True,
                    )
                with c2:
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        result_df.to_excel(writer, index=False, sheet_name=dataset.title())
                    st.download_button(
                        "📗 Télécharger Excel", buffer.getvalue(),
                        file_name=Path(output_value).with_suffix(".xlsx").name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            except Exception as exc:
                st.warning(f"⚠️ Impossible d'afficher le résultat final : {exc}")
    elif status == "failed":
        st.error(f"❌ Scraping {dataset} échoué : {state.get('error', message)}")


@st.fragment(run_every=1)
def _scraping_monitor():
    """Rafraîchit la progression sans bloquer Streamlit."""
    _show_scraping_progress()


# ============================================================
# 9. SCRAPING
# ============================================================

def scrape_books(pages):
    return _start_scraping("books", pages)


def scrape_gaaraas(pages):
    return _start_scraping("gaaraas", pages)


# ============================================================
# 11. OUTILS DASHBOARD
# Description : fonctions communes utilisées par les dashboards
# pour filtrer, rechercher, paginer et télécharger les données.
# ============================================================

def _reset_dashboard_filters(prefix):
    """
    Réinitialise les filtres en changeant leur namespace de widgets.
    Cette méthode est plus fiable que pop() pour les widgets Streamlit,
    car les valeurs des widgets sont gérées par session_state.
    """
    state_key = f"{prefix}_filter_version"
    st.session_state[state_key] = (
        int(st.session_state.get(state_key, 0)) + 1
    )
    st.rerun()


def _clean_options(series):
    """Retourne les valeurs non vides, triées, pour les multiselects."""
    if series is None:
        return []
    values = (
        series.dropna()
        .astype(str)
        .str.strip()
    )
    values = values[values != ""]
    return sorted(values.unique().tolist())


def _apply_text_search(df, query):
    """Recherche le texte saisi dans toutes les colonnes du dataset."""
    query = str(query).strip()
    if not query:
        return df

    mask = (
        df.astype(str)
        .apply(
            lambda col: col.str.contains(
                query,
                case=False,
                na=False,
                regex=False,
            )
        )
        .any(axis=1)
    )
    return df.loc[mask]


def _show_filtered_table(df, key, filename):
    """
    Affiche le résultat filtré avec pagination et permet de télécharger
    uniquement les lignes actuellement filtrées.
    """
    st.markdown("### 🔎 Données collectées")

    if df.empty:
        st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
        return

    c1, c2 = st.columns([2, 1])

    with c1:
        rows_per_page = st.selectbox(
            "Lignes par page",
            [10, 25, 50, 100],
            index=1,
            key=f"{key}_rows_v{st.session_state.get(key.split("_")[0] + "_filter_version", 0)}",
        )

    total_pages = max(
        1,
        (len(df) + rows_per_page - 1) // rows_per_page,
    )

    with c2:
        page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=min(
                int(st.session_state.get(f"{key}_page", 1)),
                total_pages,
            ),
            step=1,
            key=f"{key}_page_v{st.session_state.get(key.split("_")[0] + "_filter_version", 0)}",
        )

    start_row = (int(page) - 1) * rows_per_page
    end_row = start_row + rows_per_page
    visible = df.iloc[start_row:end_row]

    m1, m2 = st.columns(2)
    m1.metric("Résultats filtrés", f"{len(df):,}")
    m2.caption(
        f"Affichage : {start_row + 1:,}–"
        f"{min(end_row, len(df)):,} / {len(df):,} "
        f"• page {int(page)}/{total_pages}"
    )

    st.dataframe(
        visible,
        use_container_width=True,
        height=440,
        hide_index=True,
    )

    st.download_button(
        "⬇️ Télécharger les données filtrées",
        df.to_csv(index=False).encode("utf-8-sig"),
        filename,
        "text/csv",
        key=f"{key}_filtered_download",
        use_container_width=True,
    )


# ============================================================
# 12. DASHBOARD BOOKS
# Description : présente les indicateurs Books to Scrape et permet
# de filtrer par catégorie, note, prix et recherche textuelle.
# ============================================================

def books_dashboard():
    file = latest(BOOK_FILES)

    if not file:
        st.warning("Aucun dataset Books disponible.")
        return

    df = read_csv(file)

    if df is None:
        return

    st.markdown("##  Books to Scrape")
    st.markdown('<div class="df-line"></div>', unsafe_allow_html=True)

    books_filter_version = int(
        st.session_state.get("books_filter_version", 0)
    )

    # ---------------------------
    # FILTRES BOOKS
    # ---------------------------
    st.markdown("### 🎛️ Filtres")

    if st.button(
        "↺ Réinitialiser les filtres",
        key="books_reset_filters",
    ):
        _reset_dashboard_filters("books")

    f1, f2, f3 = st.columns(3)

    with f1:
        search = st.text_input(
            "🔎 Rechercher",
            placeholder="Titre, auteur, catégorie...",
            key=f"books_search_{books_filter_version}",
        )

    with f2:
        selected_categories = (
            st.multiselect(
                "🏷️ Catégories",
                _clean_options(df["category"])
                if "category" in df
                else [],
                key=f"books_categories_{books_filter_version}",
            )
            if "category" in df
            else []
        )

    with f3:
        selected_ratings = (
            st.multiselect(
                "⭐ Notes",
                ["One", "Two", "Three", "Four", "Five"],
                key=f"books_ratings_{books_filter_version}",
            )
            if "rating" in df
            else []
        )

    filtered = df.copy()

    if selected_categories and "category" in filtered:
        filtered = filtered[
            filtered["category"].astype(str).isin(selected_categories)
        ]

    if selected_ratings and "rating" in filtered:
        filtered = filtered[
            filtered["rating"].astype(str).isin(selected_ratings)
        ]

    filtered = _apply_text_search(filtered, search)

    if "price" in filtered:
        filtered["_price_num"] = pd.to_numeric(
            filtered["price"]
            .astype(str)
            .str.replace("£", "", regex=False),
            errors="coerce",
        )

        valid_price = filtered["_price_num"].dropna()

        if not valid_price.empty:
            min_price = float(valid_price.min())
            max_price = float(valid_price.max())

            # Streamlit interdit un slider lorsque min == max.
            # Ce cas apparaît notamment après un filtre très restrictif.
            if min_price < max_price:
                p1, p2 = st.columns(2)

                with p1:
                    price_range = st.slider(
                        "💷 Fourchette de prix (£)",
                        min_value=min_price,
                        max_value=max_price,
                        value=(min_price, max_price),
                        key=f"books_price_range_{books_filter_version}",
                    )

                with p2:
                    st.caption(
                        f"Prix disponible : £{min_price:.2f} → "
                        f"£{max_price:.2f}"
                    )

                filtered = filtered[
                    filtered["_price_num"].between(
                        price_range[0],
                        price_range[1],
                        inclusive="both",
                    )
                ]
            else:
                st.info(
                    f"💷 Prix unique dans la sélection : "
                    f"£{min_price:.2f}"
                )

        filtered = filtered.drop(columns=["_price_num"])

    # ---------------------------
    # KPI SUR LES DONNÉES FILTRÉES
    # ---------------------------
    st.caption(
        f"📌 {len(filtered):,} ligne(s) après application des filtres "
        f"sur {len(df):,} ligne(s) au total."
    )

    if "price" in filtered:
        price = pd.to_numeric(
            filtered["price"]
            .astype(str)
            .str.replace("£", "", regex=False),
            errors="coerce",
        )
    else:
        price = pd.Series(dtype=float)

    if "rating" in filtered:
        rating = filtered["rating"].map(
            {
                "One": 1,
                "Two": 2,
                "Three": 3,
                "Four": 4,
                "Five": 5,
            }
        )
    else:
        rating = pd.Series(dtype=float)

    a, b, c, d = st.columns(4)

    a.metric(" Livres", f"{len(filtered):,}")
    b.metric(
        "💷 Prix moyen",
        f"£{price.mean():.2f}"
        if price.notna().any()
        else "N/A",
    )
    c.metric(
        "⭐ Note moyenne",
        f"{rating.mean():.2f}/5"
        if rating.notna().any()
        else "N/A",
    )
    d.metric(
        "🏷️ Catégories",
        filtered["category"].nunique()
        if "category" in filtered
        else "N/A",
    )

    # ---------------------------
    # GRAPHIQUE
    # ---------------------------
    if "category" in filtered and not filtered.empty:
        st.markdown("### 🕷️ Livres par catégorie")
        st.bar_chart(
            filtered["category"]
            .value_counts()
            .head(15)
        )

    _show_filtered_table(
        filtered,
        "books_filtered",
        "books_filtered.csv",
    )


# ============================================================
# 13. DASHBOARD GAARAAS
# Description : présente les indicateurs Gaaraas et permet de
# filtrer par marque, boîte de vitesses, prix, kilométrage et recherche.
# ============================================================

def gaaraas_dashboard():
    file = latest(GAARAAS_FILES)

    if not file:
        st.warning("Aucun dataset Gaaraas disponible.")
        return

    df = read_csv(file)

    if df is None:
        return

    st.markdown("##  Gaaraas")
    st.markdown('<div class="df-line"></div>', unsafe_allow_html=True)

    gaaraas_filter_version = int(
        st.session_state.get("gaaraas_filter_version", 0)
    )

    # ---------------------------
    # FILTRES GAARAAS
    # ---------------------------
    st.markdown("### 🎛️ Filtres")

    if st.button(
        "↺ Réinitialiser les filtres",
        key="gaaraas_reset_filters",
    ):
        _reset_dashboard_filters("gaaraas")

    f1, f2, f3 = st.columns(3)

    with f1:
        search = st.text_input(
            "🔎 Rechercher",
            placeholder="Marque, modèle, ville...",
            key=f"gaaraas_search_{gaaraas_filter_version}",
        )

    with f2:
        selected_brands = (
            st.multiselect(
                "🏷️ Marques",
                _clean_options(df["brand"])
                if "brand" in df
                else [],
                key=f"gaaraas_brands_{gaaraas_filter_version}",
            )
            if "brand" in df
            else []
        )

    with f3:
        selected_gearboxes = (
            st.multiselect(
                "⚙️ Boîtes de vitesses",
                _clean_options(df["gearbox"])
                if "gearbox" in df
                else [],
                key=f"gaaraas_gearboxes_{gaaraas_filter_version}",
            )
            if "gearbox" in df
            else []
        )

    filtered = df.copy()

    if selected_brands and "brand" in filtered:
        filtered = filtered[
            filtered["brand"].astype(str).isin(selected_brands)
        ]

    if selected_gearboxes and "gearbox" in filtered:
        filtered = filtered[
            filtered["gearbox"].astype(str).isin(selected_gearboxes)
        ]

    filtered = _apply_text_search(filtered, search)

    # Prix
    if "price" in filtered:
        filtered["_price_num"] = pd.to_numeric(
            filtered["price"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True),
            errors="coerce",
        )

    # Kilométrage
    if "mileage" in filtered:
        filtered["_mileage_num"] = pd.to_numeric(
            filtered["mileage"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True),
            errors="coerce",
        )

    p1, p2 = st.columns(2)

    if "_price_num" in filtered and filtered["_price_num"].notna().any():
    
        price_valid = filtered["_price_num"].dropna()
    
        min_price = float(price_valid.min())
        max_price = float(price_valid.max())
    
        if min_price < max_price:
    
            with p1:
    
                price_range = st.slider(
                    "💰 Fourchette de prix",
                    min_value=min_price,
                    max_value=max_price,
                    value=(min_price, max_price),
                    key=f"gaaraas_price_range_{gaaraas_filter_version}",
                )
    
            filtered = filtered[
                filtered["_price_num"].between(
                    price_range[0],
                    price_range[1],
                    inclusive="both",
                )
            ]
    
        else:
    
            with p1:
    
                st.info(
                    f"💰 Prix unique dans la sélection : "
                    f"{min_price:,.0f}"
                )
    
        if "_mileage_num" in filtered and filtered["_mileage_num"].notna().any():
            mileage_valid = filtered["_mileage_num"].dropna()
            min_mileage = float(mileage_valid.min())
            max_mileage = float(mileage_valid.max())
    
            if min_mileage < max_mileage:
                with p2:
                    mileage_range = st.slider(
                        "🛣️ Fourchette de kilométrage",
                        min_value=min_mileage,
                        max_value=max_mileage,
                        value=(min_mileage, max_mileage),
                        key=f"gaaraas_mileage_range_{gaaraas_filter_version}",
                    )
    
                filtered = filtered[
                    filtered["_mileage_num"].between(
                        mileage_range[0],
                        mileage_range[1],
                        inclusive="both",
                    )
                ]
            else:
                with p2:
                    st.info(
                        f"🛣️ Kilométrage unique dans la sélection : "
                        f"{min_mileage:,.0f} km"
                    )
    
        # Supprimer les colonnes techniques avant affichage/téléchargement.
    technical_columns = [
        column
        for column in ["_price_num", "_mileage_num"]
        if column in filtered
    ]
    filtered = filtered.drop(columns=technical_columns)

    # ---------------------------
    # KPI SUR LES DONNÉES FILTRÉES
    # ---------------------------
    st.caption(
        f"📌 {len(filtered):,} ligne(s) après application des filtres "
        f"sur {len(df):,} ligne(s) au total."
    )

    price = (
        pd.to_numeric(
            filtered["price"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True),
            errors="coerce",
        )
        if "price" in filtered
        else pd.Series(dtype=float)
    )

    mileage = (
        pd.to_numeric(
            filtered["mileage"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True),
            errors="coerce",
        )
        if "mileage" in filtered
        else pd.Series(dtype=float)
    )

    a, b, c, d = st.columns(4)

    a.metric(" Annonces", f"{len(filtered):,}")
    b.metric(
        "💰 Prix moyen",
        f"{price.mean():,.0f} XOF"
        if price.notna().any()
        else "N/A",
    )
    c.metric(
        "🛣️ Kilométrage moyen",
        f"{mileage.mean():,.0f} km"
        if mileage.notna().any()
        else "N/A",
    )
    d.metric(
        "🏷️ Marques",
        filtered["brand"].nunique()
        if "brand" in filtered
        else "N/A",
    )

    # ---------------------------
    # GRAPHIQUES
    # ---------------------------
    if "brand" in filtered and not filtered.empty:
        st.markdown("### 🕷️ Annonces par marque")
        st.bar_chart(
            filtered["brand"]
            .value_counts()
            .head(15)
        )

    if "gearbox" in filtered and not filtered.empty:
        st.markdown("### ⚙️ Boîtes de vitesses")
        st.bar_chart(
            filtered["gearbox"]
            .value_counts()
        )

    _show_filtered_table(
        filtered,
        "gaaraas_filtered",
        "gaaraas_filtered.csv",
    )


# ============================================================
# 14. TÉLÉCHARGEMENT
# Description : permet de télécharger les datasets produits.
# ============================================================

def download_files(files):
    existing = [f for f in files if f.exists()]

    if not existing:
        st.warning("Aucun fichier disponible.")
        return

    for file in existing:
        st.download_button(
            f"⬇️ Télécharger {file.name}",
            file.read_bytes(),
            file.name,
            "text/csv",
            key=f"download_{file.name}",
            use_container_width=True,
        )


# ============================================================
# 15. BASE SQL
# Description : contrôle la base SQLite existante et permet de
# consulter les tables Books et Gaaraas.
# ============================================================

def sql_dashboard():
    st.markdown("## 🗄️ SQL Database")
    st.markdown('<div class="df-line"></div>', unsafe_allow_html=True)

    st.info(
        f"Base : `{database_path(ROOT)}` • "
        f"Taille : {_database_size(ROOT) / 1024:.1f} KB"
    )

    tables = list_tables(ROOT)

    a, b, c = st.columns(3)

    a.metric(" Books", f"{table_count(ROOT, 'books'):,}")
    b.metric(" Gaaraas", f"{table_count(ROOT, 'gaaraas'):,}")
    c.metric("🗄️ Tables", len(tables))

    if tables:
        st.dataframe(
            pd.DataFrame({"Table": tables}),
            use_container_width=True,
            hide_index=True,
        )

    data_tables = [
        table for table in tables
        if table != "database_info"
    ]

    if data_tables:
        selected = st.selectbox(
            "Table à consulter",
            data_tables,
        )

        try:
            df = read_table(ROOT, selected)
            _show_filtered_table(
                df,
                f"sql_{selected}",
                f"{selected}.csv",
            )
        except Exception as exc:
            st.error(f"Erreur de lecture SQL : {exc}")


# ============================================================
# 16. ÉVALUATION
# Description : fournit les accès aux deux formulaires demandés.
# Les URLs correspondent aux formulaires configurés dans le projet.
# ============================================================

KOBO_URL = st.session_state.df_kobo_url

GOOGLE_FORMS_URL = st.session_state.df_google_url


def evaluation_dashboard():
    st.markdown("## 🧪 Evaluate the App")
    st.markdown('<div class="df-line"></div>', unsafe_allow_html=True)

    st.info(
        "Utilisez l'un des deux formulaires prévus pour l'évaluation "
        "de l'application."
    )

    left, right = st.columns(2)

    with left:
        st.markdown(
            """
            <div class="df-form-card">
                <div class="df-form-icon">📝</div>
                <div class="df-form-title">KoboToolbox</div>
                <div class="df-form-description">
                    Formulaire d'évaluation
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.link_button(
            "📝 OUVRIR KOBOTOOLBOX",
            KOBO_URL,
            use_container_width=True,
        )

    with right:
        st.markdown(
            """
            <div class="df-form-card">
                <div class="df-form-icon">📋</div>
                <div class="df-form-title">Google Forms</div>
                <div class="df-form-description">
                    Formulaire d'évaluation
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.link_button(
            "📋 OUVRIR GOOGLE FORMS",
            GOOGLE_FORMS_URL,
            use_container_width=True,
        )

    st.markdown("### 🔍 Vérification des composants")

    components = [
        (" Books scraper", BOOKS, "required"),
        (" Gaaraas scraper", GAARAAS, "required"),
        ("⚙️ Scraper runner", RUNNER, "required"),
    ]

    for name, file, level in components:
        if file.exists():
            st.success(f"✅ {name} : disponible")
        else:
            st.error(f"❌ {name} : introuvable")

    st.info("ℹ️ La récupération des détails Books est intégrée au nouveau scraper ; aucun fichier `complete_books_details.py` séparé n'est requis.")


# ============================================================
# 17. SIDEBAR
# Description : navigation minimale entre les fonctionnalités
# prévues dans le projet.
# ============================================================

st.sidebar.title("🕷️ DATAFORGE")
st.sidebar.caption(f"📍 {st.session_state.df_location}")
st.sidebar.caption("Data Collection")

source = st.sidebar.selectbox(
    "Source de données",
    [
        " Books to Scrape",
        " Gaaraas",
    ],
)

pages = st.sidebar.number_input(
    "Pages à traiter",
    min_value=1,
    max_value=100,
    value=50 if source.startswith("") else 13,
    step=1,
)

mode = st.sidebar.selectbox(
    "Fonctionnalité",
    [
        "🚀 Scrape data",
        "⬇️ Download scraped data",
        "🕷️ Dashboard of the data",
        "🗄️ SQL Database",
        "🧪 Evaluate the App",
    ],
)

# ============================================================
# DIAGNOSTIC SELENIUM — TEMPORAIRE
# Description : vérifie Chromium et ChromeDriver directement
# sur l'environnement Streamlit Cloud.
# ============================================================

if st.sidebar.button(
    "🔧 Diagnostic Selenium",
    key="diagnostic_selenium_button",
):

    diagnostic_script = SCRAPING / "test_cloud_driver.py"

    if not diagnostic_script.exists():

        st.error(
            f"❌ Fichier introuvable : {diagnostic_script}"
        )

    else:

        try:

            result = subprocess.run(
                [
                    sys.executable,
                    str(diagnostic_script),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=120,
            )

            output = (
                result.stdout
                + "\n"
                + result.stderr
            )

            st.code(
                output,
                language="text",
            )

            if result.returncode == 0:
                st.success(
                    "✅ Diagnostic Selenium terminé."
                )
            else:
                st.error(
                    f"❌ Diagnostic terminé avec le code "
                    f"{result.returncode}."
                )

        except subprocess.TimeoutExpired:
            st.error(
                "⏱️ Le diagnostic Selenium a dépassé "
                "la limite de 120 secondes."
            )

        except Exception as exc:
            st.error(
                f"❌ Erreur pendant le diagnostic Selenium : {exc}"
            )

# ============================================================
# 18. EN-TÊTE
# Description : identité simple de l'application.
# ============================================================

st.markdown(
    f"""
    <div class="df-title">
        🕷️ MY DATA COLLECTION APP DATAFORGE
    </div>
    <div class="df-subtitle">
        {CURRENT_SUBTITLE}
    </div>
    <div class="df-line"></div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 19. SCRAPING
# Description : lance le scraper de la source sélectionnée.
# ============================================================

if mode == "🚀 Scrape data":
    st.markdown("## 🚀 Scrape data")

    st.write(
        f"Source : **{source}** • "
        f"Pages à traiter : **{pages}**"
    )

    state = _read_job_state() or {}
    running = state.get("status") in {"starting", "running"}

    if running:
        _show_scraping_progress()
    else:
        if st.button(
            "🚀 START SCRAPING",
            type="primary",
            use_container_width=True,
        ):
            started = (
                scrape_books(pages)
                if source.startswith("")
                else scrape_gaaraas(pages)
            )
            if started:
                st.success("🚀 Scraping lancé en arrière-plan.")
                st.rerun()

    # Affichage de l'état persistant. Le runner continue même si
    # l'utilisateur sélectionne une autre fonctionnalité.
    try:
        _scraping_monitor()
    except Exception:
        pass

# ============================================================
# 20. DOWNLOAD
# Description : téléchargement des CSV.
# ============================================================

elif mode == "⬇️ Download scraped data":
    st.markdown("## ⬇️ Download scraped data")

    download_files(
        BOOK_FILES
        if source.startswith("")
        else GAARAAS_FILES
    )

# ============================================================
# 21. DASHBOARD
# Description : visualisation des données nettoyées.
# ============================================================

elif mode == "🕷️ Dashboard of the data":
    if source.startswith(""):
        books_dashboard()
    else:
        gaaraas_dashboard()

# ============================================================
# 22. SQL
# Description : consultation de la base de données SQL.
# ============================================================

elif mode == "🗄️ SQL Database":
    sql_dashboard()

# ============================================================
# 23. ÉVALUATION
# Description : accès aux formulaires demandés.
# ============================================================

else:
    evaluation_dashboard()

