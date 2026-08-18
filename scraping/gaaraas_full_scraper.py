# ============================================================
# DATAFORGE — GAARAAS SCRAPER
# ============================================================
# Collecte contrôlée par plage de pages.
#
# Exemple :
#   1 page  -> scrape_all_gaaraas(1, 1)
#   5 pages -> scrape_all_gaaraas(1, 5)
#   10 pages -> scrape_all_gaaraas(1, 10)
#
# Le scraper ne reprend PAS automatiquement les anciennes
# données. Chaque nouvelle collecte recrée le CSV.
# ============================================================

from pathlib import Path
import os
import re
import time

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = (
    "https://www.gaaraas.com/fr/users/dakar-auto?page={}"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "cleaned"
    / "gaaraas_full.csv"
)

DEFAULT_START_PAGE = 1
DEFAULT_END_PAGE = 1

PAGE_LOAD_TIMEOUT = 20
ELEMENT_TIMEOUT = 10


# ============================================================
# PROGRESSION DATAFORGE
# ============================================================

STATE_FILE = (
    Path(__file__).resolve().parent.parent
    / "data" / "temp" / "dataforge_scraping_job.json"
)

def report_progress(
    *,
    dataset,
    status="running",
    stage="collection",
    current_page=0,
    total_pages=1,
    progress=0,
    message="",
    error=None,
):
    """Met à jour l'état persistant du scraping de façon atomique."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        current = {}
        if STATE_FILE.exists():
            try:
                import json
                current = json.loads(
                    STATE_FILE.read_text(encoding="utf-8")
                )
            except Exception:
                current = {}

        current.update({
            "dataset": dataset,
            "status": status,
            "stage": stage,
            "current_page": int(current_page),
            "total_pages": int(total_pages),
            "progress": max(0, min(100, int(progress))),
            "message": message,
            "error": error,
        })
        current["updated_at"] = time.time()

        tmp_file = STATE_FILE.with_suffix(".tmp")
        tmp_file.write_text(
            __import__("json").dumps(
                current, ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )
        os.replace(tmp_file, STATE_FILE)
    except Exception:
        # Une panne d'affichage de progression ne doit jamais
        # interrompre le scraping Selenium.
        pass


# ============================================================
# DRIVER SELENIUM
# ============================================================

def create_driver():

    options = Options()

    # --------------------------------------------------------
    # Détection environnement
    # --------------------------------------------------------

    is_linux = (
        os.name != "nt"
    )

    is_deployed = (
        os.environ.get(
            "STREAMLIT_SERVER_HEADLESS"
        )
        == "true"
        or is_linux
    )

    # --------------------------------------------------------
    # Mode headless pour le déploiement
    # --------------------------------------------------------

    if is_deployed:

        options.add_argument(
            "--headless=new"
        )

        options.add_argument(
            "--no-sandbox"
        )

        options.add_argument(
            "--disable-dev-shm-usage"
        )

        options.add_argument(
            "--disable-gpu"
        )

        options.add_argument(
            "--disable-software-rasterizer"
        )

        options.add_argument(
            "--window-size=1920,1080"
        )

    else:

        options.add_argument(
            "--start-maximized"
        )

    # --------------------------------------------------------
    # Optimisations Chrome
    # --------------------------------------------------------

    options.add_argument(
        "--disable-notifications"
    )

    options.add_argument(
        "--disable-popup-blocking"
    )

    options.add_argument(
        "--disable-extensions"
    )

    options.add_argument(
        "--disable-infobars"
    )

    options.add_argument(
        "--disable-background-networking"
    )

    options.add_argument(
        "--disable-background-timer-throttling"
    )

    options.add_argument(
        "--disable-renderer-backgrounding"
    )

    options.add_argument(
        "--disable-features=Translate"
    )

    options.add_argument(
        "--log-level=3"
    )

    # --------------------------------------------------------
    # Réduire les ressources inutiles
    # --------------------------------------------------------

    options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
        },
    )

    # --------------------------------------------------------
    # Chromium / Chrome éventuel en déploiement
    # --------------------------------------------------------

    browser_binary = (
        os.environ.get("CHROME_BIN")
        or os.environ.get("CHROMIUM_BIN")
    )

    if browser_binary and Path(
        browser_binary
    ).exists():

        options.binary_location = (
            browser_binary
        )

    # --------------------------------------------------------
    # Création du driver
    # --------------------------------------------------------

    driver = webdriver.Chrome(
        options=options
    )

    driver.set_page_load_timeout(
        PAGE_LOAD_TIMEOUT
    )

    return driver


# ============================================================
# NETTOYAGE TEXTE
# ============================================================

def clean_text(text):

    if not text:
        return ""

    return " ".join(
        str(text).split()
    ).strip()


# ============================================================
# EXTRACTION D'UNE VALEUR
# ============================================================

def extract_detail_value(
    body,
    field,
):

    lines = [
        clean_text(line)
        for line in body.splitlines()
        if clean_text(line)
    ]

    field_upper = (
        clean_text(field)
        .upper()
    )

    for i, line in enumerate(lines):

        if line.upper() == field_upper:

            if i + 1 < len(lines):
                candidate = lines[i + 1]

                if candidate.strip().lower() not in {
                    "notre histoire",
                    "our story",
                }:
                    return candidate

    return ""


# ============================================================
# PRIX
# ============================================================

def extract_price(text):

    if not text:
        return None

    # Gestion CFA / FCFA / espaces
    patterns = [
        r"CFA\s*([\d\s]+)",
        r"([\d\s]+)\s*CFA",
        r"FCFA\s*([\d\s]+)",
        r"([\d\s]+)\s*FCFA",
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not matches:
            continue

        value = (
            matches[-1]
            .replace(" ", "")
            .replace("\u00a0", "")
            .strip()
        )

        try:

            return int(value)

        except ValueError:

            continue

    return None


# ============================================================
# FALLBACK NOM VEHICULE DEPUIS L'URL
# ============================================================

def extract_vehicle_name_from_url(listing_url, region=""):
    """
    Fallback lorsque le site renvoie un titre générique comme
    'Notre histoire' au lieu du nom du véhicule.

    Exemple :
    annonce-peugeot-207-dakar-dakar-908
    -> Peugeot / 207
    """
    if not listing_url:
        return ""

    try:
        from urllib.parse import urlparse, unquote

        path = unquote(urlparse(listing_url).path)
        slug = path.rstrip("/").split("/")[-1].lower()

        if not slug.startswith("annonce-"):
            return ""

        slug = slug[len("annonce-"):]

        # Retirer l'identifiant final.
        parts = slug.split("-")
        if parts and parts[-1].isdigit():
            parts = parts[:-1]

        region_clean = clean_text(region).lower()

        # Le site utilise généralement ...-region-region-id.
        if region_clean:
            region_parts = region_clean.split()
            n = len(region_parts)
            if n and len(parts) >= 2 * n:
                if parts[-2*n:-n] == region_parts and parts[-n:] == region_parts:
                    parts = parts[:-2*n]

        # Fallback générique : retirer deux dernières occurrences
        # si elles ressemblent à une région.
        if len(parts) >= 3 and parts[-1] == parts[-2]:
            parts = parts[:-2]

        if not parts:
            return ""

        return " ".join(
            item.capitalize()
            for item in parts
        )

    except Exception:
        return ""


# ============================================================
# NOM DU VEHICULE
# ============================================================

def extract_vehicle_name(body, listing_url="", region=""):

    lines = [
        clean_text(line)
        for line in body.splitlines()
        if clean_text(line)
    ]

    # --------------------------------------------------------
    # Cas encodage historique du site
    # --------------------------------------------------------

    for line in lines:

        if line.startswith(
            "DÃ©tails"
        ):

            name = line.replace(
                "DÃ©tails",
                "",
                1,
            ).strip()

            if name and name.strip().lower() not in {
                "notre histoire",
                "our story",
            }:

                return name

    # --------------------------------------------------------
    # Cas "Détails"
    # --------------------------------------------------------

    for i, line in enumerate(lines):

        if line.lower() in {
            "détails",
            "details",
        }:

            if i + 1 < len(lines):
                candidate = lines[i + 1].strip()

                # Le site place parfois "Notre histoire" juste après
                # "Détails". Ce n'est pas le nom du véhicule.
                if candidate.lower() not in {
                    "notre histoire",
                    "our story",
                }:
                    return candidate

    # --------------------------------------------------------
    # Recherche approximative
    # --------------------------------------------------------

    for line in lines:

        if (
            "détails" in line.lower()
            or "details" in line.lower()
        ):

            value = re.sub(
                r"^.*?(détails|details)",
                "",
                line,
                flags=re.IGNORECASE,
            ).strip()

            if value and value.strip().lower() not in {
                "notre histoire",
                "our story",
            }:

                return value

    # Le site peut afficher un titre générique ("Notre histoire").
    # Dans ce cas, reconstruire le nom depuis l'URL de l'annonce.
    fallback = extract_vehicle_name_from_url(
        listing_url,
        region,
    )

    if fallback:
        return fallback

    return ""


# ============================================================
# MARQUE + MODELE
# ============================================================

def split_brand_model(
    vehicle_name
):

    vehicle_name = clean_text(
        vehicle_name
    )

    if not vehicle_name:

        return "", ""

    multiword_brands = [
        "Land Rover",
        "Alfa Romeo",
        "Mercedes Benz",
        "Mercedes-Benz",
        "Aston Martin",
        "Rolls Royce",
        "Rolls-Royce",
    ]

    for brand in multiword_brands:

        if vehicle_name.lower().startswith(
            brand.lower()
        ):

            model = (
                vehicle_name[
                    len(brand):
                ].strip()
            )

            return brand, model

    parts = vehicle_name.split()

    if len(parts) == 1:

        return parts[0], ""

    return (
        parts[0],
        " ".join(
            parts[1:]
        ),
    )


# ============================================================
# ANNEE
# ============================================================

def clean_year(
    value
):

    if not value:

        return None

    value = clean_text(
        value
    )

    if value.upper() in {
        "N/A",
        "NA",
        "N.A.",
        "-",
    }:

        return None

    match = re.search(
        r"\b(19|20)\d{2}\b",
        value,
    )

    if match:

        try:

            return int(
                match.group()
            )

        except ValueError:

            return None

    return None


# ============================================================
# KILOMETRAGE
# ============================================================

def clean_mileage(
    value
):

    if not value:

        return None

    value = clean_text(
        value
    )

    if value.upper() in {
        "N/A",
        "NA",
        "N.A.",
        "-",
    }:

        return None

    match = re.search(
        r"([\d\s]+)",
        value,
    )

    if not match:

        return None

    number = (
        match.group(1)
        .replace(" ", "")
        .replace("\u00a0", "")
    )

    try:

        return int(
            number
        )

    except ValueError:

        return None


# ============================================================
# REGION
# ============================================================

def get_region(
    body
):

    lines = [
        clean_text(line)
        for line in body.splitlines()
        if clean_text(line)
    ]

    for line in lines:

        if line.lower() == "dakar":

            return "Dakar"

    return ""


# ============================================================
# URLS DES ANNONCES
# ============================================================

def get_listing_urls(
    driver
):

    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "a[href*='/vehicle_listings/']",
    )

    urls = []

    seen = set()

    for element in elements:

        try:

            href = element.get_attribute(
                "href"
            )

        except Exception:

            continue

        if not href:

            continue

        href = href.strip()

        if not href:

            continue

        if href in seen:

            continue

        seen.add(
            href
        )

        urls.append(
            href
        )

    return urls


# ============================================================
# ATTENDRE LES ANNONCES
# ============================================================

def wait_for_listing_urls(
    driver
):

    try:

        WebDriverWait(
            driver,
            ELEMENT_TIMEOUT,
        ).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "a[href*='/vehicle_listings/']",
                )
            )
        )

    except TimeoutException:

        return []

    return get_listing_urls(
        driver
    )


# ============================================================
# SCRAPER D'UNE PAGE
# ============================================================

def scrape_page(
    driver,
    page_number,
):

    url = BASE_URL.format(
        page_number
    )

    print(
        f"\nPage {page_number}"
    )

    try:

        driver.get(
            url
        )

    except TimeoutException:

        print(
            f"Timeout page {page_number}"
        )

        try:
            driver.execute_script(
                "window.stop();"
            )
        except Exception:
            pass

    listing_urls = (
        wait_for_listing_urls(
            driver
        )
    )

    print(
        f"Annonces trouvées : "
        f"{len(listing_urls)}"
    )

    if not listing_urls:

        return []

    page_data = []

    for position, listing_url in enumerate(
        listing_urls,
        start=1,
    ):

        print(
            f"  [{position}/{len(listing_urls)}]"
        )

        try:

            driver.get(
                listing_url
            )

            # Attendre simplement le body
            WebDriverWait(
                driver,
                ELEMENT_TIMEOUT,
            ).until(
                EC.presence_of_element_located(
                    (
                        By.TAG_NAME,
                        "body",
                    )
                )
            )

            body = driver.find_element(
                By.TAG_NAME,
                "body",
            ).text

            body = body or ""

            # La région peut servir de secours pour reconstruire
            # le nom du véhicule depuis l'URL.
            region = get_region(body)

            vehicle_name = (
                extract_vehicle_name(
                    body,
                    listing_url=listing_url,
                    region=region,
                )
            )

            brand, model = (
                split_brand_model(
                    vehicle_name
                )
            )

            year = clean_year(
                extract_detail_value(
                    body,
                    "ANNÉE",
                )
            )

            # Compatibilité avec mauvais encodage
            if year is None:

                year = clean_year(
                    extract_detail_value(
                        body,
                        "ANNÃ‰E",
                    )
                )

            mileage = clean_mileage(
                extract_detail_value(
                    body,
                    "KILOMÉTRAGE",
                )
            )

            if mileage is None:

                mileage = clean_mileage(
                    extract_detail_value(
                        body,
                        "KILOMÃ‰TRAGE",
                    )
                )

            gearbox = extract_detail_value(
                body,
                "BOÎTE DE VITESSES",
            )

            if not gearbox:

                gearbox = extract_detail_value(
                    body,
                    "BOÃŽTE DE VITESSES",
                )

            gearbox = clean_text(
                gearbox
            )

            if gearbox.upper() in {
                "N/A",
                "NA",
                "-",
            }:

                gearbox = ""

            price = extract_price(
                body
            )

            page_data.append(
                {
                    "page": page_number,
                    "position_page": position,
                    "brand": brand,
                    "model": model,
                    "year": year,
                    "price": price,
                    "mileage": mileage,
                    "gearbox": gearbox,
                    "region": region,
                    "listing_url": listing_url,
                }
            )

            print(
                f"      OK "
                f"{brand} {model}"
            )

        except Exception as exc:

            print(
                f"      ERREUR : "
                f"{str(exc)[:150]}"
            )

    return page_data


# ============================================================
# SCRAPING COMPLET AVEC PLAGE DE PAGES
# ============================================================

def scrape_all_gaaraas(
    start_page=DEFAULT_START_PAGE,
    end_page=DEFAULT_END_PAGE,
):

    start_page = int(
        start_page
    )

    end_page = int(
        end_page
    )

    if start_page < 1:

        raise ValueError(
            "start_page doit être >= 1"
        )

    if end_page < start_page:

        raise ValueError(
            "end_page doit être >= start_page"
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "DATAFORGE — GAARAAS"
    )

    print(
        "=" * 70
    )

    print(
        f"Pages demandées : "
        f"{start_page} → {end_page}"
    )

    driver = None

    all_data = []

    started_at = time.time()

    try:

        driver = create_driver()

        # ----------------------------------------------------
        # TRAITEMENT PAGE PAR PAGE
        # ----------------------------------------------------

        total_pages = end_page - start_page + 1

        report_progress(
            dataset="gaaraas",
            status="running",
            stage="collection",
            current_page=0,
            total_pages=total_pages,
            progress=0,
            message=f"Collecte Gaaraas démarrée — 0/{total_pages} page(s).",
        )

        pages_completed = []

        for page_number in range(
            start_page,
            end_page + 1,
        ):

            page_data = scrape_page(
                driver,
                page_number,
            )

            if page_data:

                all_data.extend(
                    page_data
                )
                pages_completed.append(page_number)

            completed = len(pages_completed)
            progress = int(completed * 100 / total_pages)

            print(
                f"Page {page_number} terminée : "
                f"{len(page_data)} annonce(s)"
            )

            report_progress(
                dataset="gaaraas",
                status="running",
                stage="page_terminee" if page_data else "page_vide",
                current_page=completed,
                total_pages=total_pages,
                progress=progress,
                message=(
                    f"Gaaraas : page {page_number} terminée — "
                    f"{completed}/{total_pages} page(s), "
                    f"{len(all_data)} annonce(s) collectée(s)."
                ),
            )

        # ----------------------------------------------------
        # DATAFRAME
        # ----------------------------------------------------

        columns = [
            "page",
            "position_page",
            "brand",
            "model",
            "year",
            "price",
            "mileage",
            "gearbox",
            "region",
            "listing_url",
        ]

        df = pd.DataFrame(
            all_data,
            columns=columns,
        )

        # ----------------------------------------------------
        # SUPPRIMER LES DOUBLONS
        # ----------------------------------------------------

        if not df.empty:

            df = df.drop_duplicates(
                subset=[
                    "listing_url"
                ],
                keep="first",
            ).reset_index(
                drop=True
            )

        # ----------------------------------------------------
        # DOSSIER
        # ----------------------------------------------------

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # SAUVEGARDE
        # ----------------------------------------------------

        df.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig",
        )

        duration = (
            time.time()
            - started_at
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "COLLECTE GAARAAS TERMINÉE"
        )

        print(
            "=" * 70
        )

        print(
            f"Pages réellement collectées : "
            f"{df['page'].nunique() if not df.empty else 0}"
        )

        print(
            f"Annonces collectées : "
            f"{len(df)}"
        )

        print(
            f"Colonnes : "
            f"{len(df.columns)}"
        )

        print(
            f"Durée : "
            f"{duration:.1f} secondes"
        )

        print(
            f"Fichier : "
            f"{OUTPUT_FILE}"
        )

        report_progress(
            dataset="gaaraas",
            status="running",
            stage="collection_terminee",
            current_page=len(pages_completed),
            total_pages=total_pages,
            progress=int(len(pages_completed) * 100 / total_pages),
            message=(
                f"Collection Gaaraas terminée — "
                f"{len(pages_completed)}/{total_pages} page(s)."
            ),
        )

        return (
            df,
            duration,
            pages_completed,
        )

    finally:

        if driver is not None:

            try:

                driver.quit()

            except Exception:

                pass


# ============================================================
# ALIAS COMPATIBILITE
# ============================================================

def scrape_all(
    start_page=1,
    end_page=1,
):

    return scrape_all_gaaraas(
        start_page,
        end_page,
    )


# ============================================================
# MAIN
# ============================================================

def main(
    start_page=None,
    end_page=None,
):

    # --------------------------------------------------------
    # Arguments Python :
    #
    # python gaaraas_full_scraper.py 1 1
    # python gaaraas_full_scraper.py 1 5
    # --------------------------------------------------------

    if start_page is None:

        start_page = DEFAULT_START_PAGE

    if end_page is None:

        end_page = DEFAULT_END_PAGE

    return scrape_all_gaaraas(
        start_page,
        end_page,
    )


# ============================================================
# EXECUTION DIRECTE
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) >= 3:

        start = int(
            sys.argv[1]
        )

        end = int(
            sys.argv[2]
        )

    elif len(sys.argv) == 2:

        start = int(
            sys.argv[1]
        )

        end = start

    else:

        start = 1
        end = 1

    main(
        start,
        end,
    )