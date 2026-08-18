"""DataForge — Streamlit application for the Data Collection exam.

The interface follows the assignment exactly:
1. Selenium scraping + cleaning for Books to Scrape and Gaaraas
2. Download of raw Web Scraper data (no-code)
3. Dashboard of cleaned Selenium data
4. SQL database
5. Kobo + Google Forms evaluation links
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from data_database import database_path, init_database, list_tables, read_table, table_count

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
CLEANED = ROOT / "data" / "cleaned"
TEMP = ROOT / "data" / "temp"
STATE_FILE = TEMP / "dataforge_scraping_job.json"
LOCK_FILE = TEMP / "dataforge_scraping_job.lock"

BOOKS_RAW = RAW / "books_raw_webscraper.csv"
GAARAAS_RAW = RAW / "gaaraas_raw_webscraper.csv"
BOOKS_CLEAN = CLEANED / "books_clean.csv"
GAARAAS_CLEAN = CLEANED / "gaaraas_clean.csv"

KOBO_URL = "https://ee.kobotoolbox.org/x/1oNIZ8OJ"
GOOGLE_FORMS_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLScFmWJm7vxf0UYLhoVV1rV4UBpOADke6rzt1CrV4rgnFE2Wmg/"
    "viewform?usp=header"
)

BOOKS_MAX_PAGES = 50
GAARAAS_MAX_PAGES = 100
GAARAAS_CURRENT_OBSERVED_PAGES = 13

st.set_page_config(
    page_title="DataForge — Data Collection",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_database(ROOT)


def load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception as exc:
        st.error(f"Impossible de lire {path.name}: {exc}")
        return None


def read_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def is_job_running() -> bool:
    state = read_state()
    if state.get("status") not in {"starting", "running"}:
        return False
    updated = float(state.get("updated_at", 0) or 0)
    # A stale state must not lock the interface forever.
    return (time.time() - updated) < 3600


def start_scraping(dataset: str, pages: int) -> tuple[bool, str]:
    TEMP.mkdir(parents=True, exist_ok=True)
    if is_job_running():
        return False, "Un scraping est déjà en cours."

    log_path = TEMP / f"scraping_{dataset}.log"
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [sys.executable, str(ROOT / "scraper_runner.py"), dataset, str(pages), str(ROOT)]
    try:
        with log_path.open("w", encoding="utf-8") as log:
            kwargs = {
                "cwd": str(ROOT),
                "stdin": subprocess.DEVNULL,
                "stdout": log,
                "stderr": subprocess.STDOUT,
                "env": env,
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            else:
                kwargs["start_new_session"] = True
            subprocess.Popen(cmd, **kwargs)
        return True, f"Scraping {dataset} démarré en arrière-plan."
    except Exception as exc:
        return False, f"Impossible de démarrer le scraping: {exc}"


def row_count(path: Path) -> int:
    df = load_csv(path)
    return 0 if df is None else len(df)


def dataframe_download(df: pd.DataFrame, filename: str) -> None:
    st.download_button(
        "⬇️ Télécharger CSV",
        data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    return buffer.getvalue()


def render_job_status() -> None:
    state = read_state()
    if not state:
        return
    status = state.get("status", "")
    if status not in {"starting", "running", "completed", "failed"}:
        return

    label = state.get("message", "Scraping…")
    progress = max(0, min(100, int(state.get("progress", 0) or 0)))
    dataset = state.get("dataset", "").upper()
    pages = int(state.get("total_pages", 0) or 0)
    current = int(state.get("current_page", 0) or 0)

    if status in {"starting", "running"}:
        st.info(f"🔄 **{dataset}** — {label}")
        st.progress(progress / 100, text=f"{progress}% • page {current}/{pages}")
        st.caption("Le scraping est exécuté dans un processus séparé : changer de page ou relancer Streamlit ne l'arrête pas.")
    elif status == "completed":
        st.success(f"✅ {label}")
        st.progress(1.0, text="100% • terminé")
    else:
        st.error(f"❌ {label} {state.get('error', '')}")


@st.fragment(run_every="2s")
def job_monitor() -> None:
    render_job_status()


def quality_card(df: pd.DataFrame, label: str) -> None:
    missing = int(df.isna().sum().sum())
    duplicates = int(df.duplicated().sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Lignes", f"{len(df):,}")
    c2.metric("Valeurs manquantes", f"{missing:,}")
    c3.metric("Doublons exacts", f"{duplicates:,}")
    st.caption(f"Dataset : {label} • {len(df.columns)} colonnes")


def books_dashboard() -> None:
    df = load_csv(BOOKS_CLEAN)
    if df is None or df.empty:
        st.warning("Aucun dataset Books nettoyé disponible. Lancez d'abord un scraping Selenium.")
        return

    st.subheader("📚 Dashboard — Books to Scrape")
    quality_card(df, "Selenium + nettoyage")

    c1, c2, c3 = st.columns(3)
    categories = sorted(df["category"].dropna().astype(str).unique()) if "category" in df else []
    ratings = sorted(pd.to_numeric(df["rating"], errors="coerce").dropna().unique().tolist()) if "rating" in df else []
    with c1:
        selected_categories = st.multiselect("Catégorie", categories)
    with c2:
        selected_ratings = st.multiselect("Note", ratings, format_func=lambda x: f"{int(x)}/5")
    with c3:
        query = st.text_input("Recherche", placeholder="Titre, catégorie, description…")

    filtered = df.copy()
    if selected_categories:
        filtered = filtered[filtered["category"].astype(str).isin(selected_categories)]
    if selected_ratings:
        filtered = filtered[pd.to_numeric(filtered["rating"], errors="coerce").isin(selected_ratings)]
    if query:
        mask = filtered.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]

    price = pd.to_numeric(filtered.get("price"), errors="coerce")
    rating = pd.to_numeric(filtered.get("rating"), errors="coerce")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📚 Livres", f"{len(filtered):,}")
    k2.metric("💷 Prix moyen", f"£{price.mean():.2f}" if price.notna().any() else "N/A")
    k3.metric("⭐ Note moyenne", f"{rating.mean():.2f}/5" if rating.notna().any() else "N/A")
    k4.metric("🏷️ Catégories", int(filtered["category"].nunique()) if "category" in filtered else 0)

    a, b = st.columns(2)
    with a:
        if "category" in filtered and not filtered.empty:
            st.markdown("**Livres par catégorie**")
            st.bar_chart(filtered["category"].value_counts().head(12))
    with b:
        if "rating" in filtered and not filtered.empty:
            st.markdown("**Répartition des notes**")
            st.bar_chart(pd.to_numeric(filtered["rating"], errors="coerce").value_counts().sort_index())

    st.markdown("### Tableau des données nettoyées")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    dataframe_download(filtered, "books_clean_filtered.csv")


def gaaraas_dashboard() -> None:
    df = load_csv(GAARAAS_CLEAN)
    if df is None or df.empty:
        st.warning("Aucun dataset Gaaraas nettoyé disponible. Lancez d'abord un scraping Selenium.")
        return

    st.subheader("🚗 Dashboard — Gaaraas")
    quality_card(df, "Selenium + nettoyage")

    c1, c2, c3 = st.columns(3)
    brands = sorted(df["brand"].dropna().astype(str).unique()) if "brand" in df else []
    gearboxes = sorted(df["gearbox"].dropna().astype(str).unique()) if "gearbox" in df else []
    with c1:
        selected_brands = st.multiselect("Marque", brands)
    with c2:
        selected_gearboxes = st.multiselect("Boîte de vitesses", gearboxes)
    with c3:
        query = st.text_input("Recherche", placeholder="Marque, modèle, région…")

    filtered = df.copy()
    if selected_brands:
        filtered = filtered[filtered["brand"].astype(str).isin(selected_brands)]
    if selected_gearboxes:
        filtered = filtered[filtered["gearbox"].astype(str).isin(selected_gearboxes)]
    if query:
        mask = filtered.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]

    price = pd.to_numeric(filtered.get("price"), errors="coerce")
    mileage = pd.to_numeric(filtered.get("mileage"), errors="coerce")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🚗 Annonces", f"{len(filtered):,}")
    k2.metric("💰 Prix moyen", f"{price.mean():,.0f} CFA" if price.notna().any() else "N/A")
    k3.metric("🛣️ Kilométrage moyen", f"{mileage.mean():,.0f} km" if mileage.notna().any() else "N/A")
    k4.metric("🏷️ Marques", int(filtered["brand"].nunique()) if "brand" in filtered else 0)

    a, b = st.columns(2)
    with a:
        if "brand" in filtered and not filtered.empty:
            st.markdown("**Top marques**")
            st.bar_chart(filtered["brand"].value_counts().head(12))
    with b:
        if "gearbox" in filtered and not filtered.empty:
            st.markdown("**Boîtes de vitesses**")
            st.bar_chart(filtered["gearbox"].value_counts())

    st.markdown("### Tableau des données nettoyées")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    dataframe_download(filtered, "gaaraas_clean_filtered.csv")


def download_page(source: str) -> None:
    st.subheader("⬇️ Téléchargement des données")
    st.caption("Les fichiers RAW correspondent au scraping no-code Web Scraper et ne sont volontairement pas nettoyés.")

    raw = BOOKS_RAW if source == "books" else GAARAAS_RAW
    clean = BOOKS_CLEAN if source == "books" else GAARAAS_CLEAN
    raw_df = load_csv(raw)
    clean_df = load_csv(clean)

    a, b = st.columns(2)
    with a:
        st.markdown("### 🧾 RAW — Web Scraper (no-code)")
        if raw_df is not None:
            st.metric("Lignes", f"{len(raw_df):,}")
            st.download_button("⬇️ Télécharger le RAW CSV", raw.read_bytes(), raw.name, "text/csv", use_container_width=True)
            st.dataframe(raw_df.head(20), use_container_width=True, hide_index=True)
        else:
            st.warning("Fichier RAW absent.")
    with b:
        st.markdown("### 🧹 CLEAN — Selenium")
        if clean_df is not None:
            st.metric("Lignes", f"{len(clean_df):,}")
            st.download_button("⬇️ Télécharger le CLEAN CSV", clean.read_bytes(), clean.name, "text/csv", use_container_width=True)
            st.download_button("⬇️ Télécharger le CLEAN Excel", excel_bytes(clean_df), clean.stem + ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            st.dataframe(clean_df.head(20), use_container_width=True, hide_index=True)
        else:
            st.warning("Fichier CLEAN absent.")


def sql_page() -> None:
    st.subheader("🗄️ Base de données SQL")
    st.info(f"SQLite : `{database_path(ROOT)}`")
    c1, c2, c3 = st.columns(3)
    c1.metric("Books", f"{table_count(ROOT, 'books'):,}")
    c2.metric("Gaaraas", f"{table_count(ROOT, 'gaaraas'):,}")
    c3.metric("Tables", len(list_tables(ROOT)))

    table = st.selectbox("Table à consulter", ["books", "gaaraas"])
    df = read_table(ROOT, table)
    st.dataframe(df, use_container_width=True, hide_index=True)
    dataframe_download(df, f"{table}_sql.csv")


def evaluation_page() -> None:
    st.subheader("🧪 Évaluation de l'application")
    st.write("Les deux formulaires demandés par le sujet sont accessibles directement ci-dessous.")
    a, b = st.columns(2)
    with a:
        st.link_button("📝 Ouvrir KoboToolbox", KOBO_URL, use_container_width=True)
    with b:
        st.link_button("📋 Ouvrir Google Forms", GOOGLE_FORMS_URL, use_container_width=True)
    st.info("Les questions, sections et logiques conditionnelles des formulaires dépendent du document de spécification séparé fourni par l'enseignant.")


def home_page() -> None:
    st.subheader("Projet d'examen — Data Collection")
    st.markdown("**Web scraping, nettoyage de données et déploiement Streamlit**")
    st.write("DataForge regroupe la collecte Selenium, le nettoyage pandas, le stockage SQL, le téléchargement des données Web Scraper et la visualisation.")

    st.markdown("### ✅ Correspondance avec le sujet")
    rows = [
        ("Books to Scrape", "Selenium", "50 pages", "books_clean.csv"),
        ("Gaaraas", "Selenium", "jusqu'à 100 pages", "gaaraas_clean.csv"),
        ("Web Scraper", "No-code", "RAW", "data/raw/*.csv"),
        ("Dashboard", "Streamlit", "Données Selenium nettoyées", "2 dashboards"),
        ("SQL", "SQLite", "2 tables", "data/database/data_collection.db"),
        ("Évaluation", "Kobo + Google Forms", "2 liens", "Écran Évaluation"),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Exigence", "Méthode", "Périmètre", "Livrable"]), use_container_width=True, hide_index=True)

    st.markdown("### ℹ️ État de la source Gaaraas")
    st.warning(
        f"Le sujet demande 100 pages. Lors de l'audit du projet, Gaaraas affichait actuellement {GAARAAS_CURRENT_OBSERVED_PAGES} pages pour Dakar auto. "
        "L'application reste configurable jusqu'à 100 pages afin de respecter la consigne : les pages sans annonces sont simplement signalées comme vides."
    )

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Books CLEAN", f"{row_count(BOOKS_CLEAN):,}")
    b2.metric("Gaaraas CLEAN", f"{row_count(GAARAAS_CLEAN):,}")
    b3.metric("Books RAW", f"{row_count(BOOKS_RAW):,}")
    b4.metric("Gaaraas RAW", f"{row_count(GAARAAS_RAW):,}")


# Sidebar
st.sidebar.title("🕷️ DATAFORGE")
st.sidebar.caption("Projet d'examen — Data Collection")
source_label = st.sidebar.selectbox("Source de données", ["📚 Books to Scrape", "🚗 Gaaraas"])
source = "books" if source_label.startswith("📚") else "gaaraas"
max_pages = BOOKS_MAX_PAGES if source == "books" else GAARAAS_MAX_PAGES
default_pages = BOOKS_MAX_PAGES if source == "books" else GAARAAS_MAX_PAGES
pages = st.sidebar.number_input("Pages à traiter", min_value=1, max_value=max_pages, value=default_pages, step=1)
mode = st.sidebar.selectbox("Fonctionnalité", [
    "🏠 Présentation",
    "🚀 Scraping Selenium",
    "⬇️ Données RAW / CLEAN",
    "🕷️ Dashboard",
    "🗄️ SQL Database",
    "🧪 Évaluation",
])
st.sidebar.divider()
st.sidebar.caption("Books : 50 pages • Gaaraas : jusqu'à 100 pages")

st.title("🕷️ DATAFORGE — DATA COLLECTION")
st.caption("Web scraping • nettoyage • SQL • dashboard • évaluation")
st.divider()

if mode == "🏠 Présentation":
    home_page()
elif mode == "🚀 Scraping Selenium":
    st.subheader("🚀 Scraping Selenium")
    st.write(f"Source sélectionnée : **{source_label}** • **{pages} page(s)**")
    if source == "gaaraas" and pages == 100:
        st.warning("La consigne demande 100 pages. La source observée actuellement n'en expose qu'environ 13 ; les pages restantes seront contrôlées puis signalées vides.")
    if st.button("🚀 START SCRAPING", type="primary", use_container_width=True, disabled=is_job_running()):
        ok, message = start_scraping(source, int(pages))
        (st.success if ok else st.error)(message)
    st.markdown("### Progression")
    job_monitor()
elif mode == "⬇️ Données RAW / CLEAN":
    download_page(source)
elif mode == "🕷️ Dashboard":
    books_dashboard() if source == "books" else gaaraas_dashboard()
elif mode == "🗄️ SQL Database":
    sql_page()
elif mode == "🧪 Évaluation":
    evaluation_page()
