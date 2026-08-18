# ============================================================
# DATAFORGE — SCRAPER RUNNER
# ============================================================
# Usage:
#   python scraper_runner.py books 1 /chemin/DataForge
#   python scraper_runner.py gaaraas 13 /chemin/DataForge
#
# Ce fichier est volontairement séparé de Streamlit.
# Le scraping peut donc continuer indépendamment des reruns
# de l'interface.
# ============================================================

import importlib.util
import json
import os
import sys
import time
from pathlib import Path


def write_state(state_file: Path, **values):
    state_file.parent.mkdir(parents=True, exist_ok=True)

    current = {}
    if state_file.exists():
        try:
            current = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            current = {}

    current.update(values)
    current["updated_at"] = time.time()

    state_file.write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_module(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Script introuvable : {path}")

    module_name = f"dataforge_scraper_{path.stem}"

    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de charger : {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configure_pages(module, pages):
    # Les différents scrapers existants peuvent utiliser des noms
    # différents. On renseigne tous les noms connus.
    for name, value in {
        "START_PAGE": 1,
        "END_PAGE": pages,
        "MAX_PAGES": pages,
        "PAGES": pages,
    }.items():
        setattr(module, name, value)


def run_books(root: Path, pages: int, state_file: Path):
    script = root / "scraping" / "books_scraper.py"
    details = root / "scraping" / "complete_books_details.py"

    if not script.exists():
        raise FileNotFoundError(f"books_scraper.py introuvable : {script}")

    write_state(
        state_file,
        dataset="books",
        status="running",
        stage="catalogue",
        pages=pages,
        current_page=0,
        total_pages=pages,
        message=f"Collecte Books : {pages} page(s)",
    )

    module = load_module(script)
    configure_pages(module, pages)

    if hasattr(module, "scrape_all_books"):
        module.scrape_all_books(1, pages)
    elif hasattr(module, "main"):
        module.main()
    else:
        raise RuntimeError(
            "books_scraper.py ne contient ni scrape_all_books() ni main()."
        )

    output = root / "data" / "cleaned" / "books_full.csv"

    if not output.exists():
        raise RuntimeError(
            "Le scraper Books n'a pas produit data/cleaned/books_full.csv."
        )

    if details.exists():
        write_state(
            state_file,
            stage="details",
            current_page=pages,
            message="Récupération des détails des livres...",
        )

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        import subprocess

        result = subprocess.run(
            [sys.executable, str(details)],
            cwd=str(root),
            env=env,
        )

        if result.returncode != 0:
            raise RuntimeError("complete_books_details.py a échoué.")

    write_state(
        state_file,
        dataset="books",
        status="completed",
        stage="finished",
        pages=pages,
        current_page=pages,
        total_pages=pages,
        output=str(output),
        message=f"Books terminé : {pages} page(s).",
    )


def run_gaaraas(root: Path, pages: int, state_file: Path):
    script = root / "scraping" / "gaaraas_full_scraper.py"

    if not script.exists():
        raise FileNotFoundError(f"gaaraas_full_scraper.py introuvable : {script}")

    write_state(
        state_file,
        dataset="gaaraas",
        status="running",
        stage="collection",
        pages=pages,
        current_page=0,
        total_pages=pages,
        message=f"Collecte Gaaraas : {pages} page(s)",
    )

    module = load_module(script)
    configure_pages(module, pages)

    if hasattr(module, "scrape_all_gaaraas"):
        module.scrape_all_gaaraas(1, pages)
    elif hasattr(module, "scrape_all"):
        module.scrape_all(1, pages)
    elif hasattr(module, "main"):
        module.main()
    else:
        raise RuntimeError(
            "gaaraas_full_scraper.py ne contient aucune fonction compatible."
        )

    output = root / "data" / "cleaned" / "gaaraas_full.csv"

    if not output.exists():
        raise RuntimeError(
            "Le scraper Gaaraas n'a pas produit data/cleaned/gaaraas_full.csv."
        )

    write_state(
        state_file,
        dataset="gaaraas",
        status="completed",
        stage="finished",
        pages=pages,
        current_page=pages,
        total_pages=pages,
        output=str(output),
        message=f"Gaaraas terminé : {pages} page(s).",
    )


def main():
    if len(sys.argv) != 4:
        print(
            "Usage : python scraper_runner.py "
            "<books|gaaraas> <pages> <root>"
        )
        raise SystemExit(2)

    dataset = sys.argv[1].strip().lower()

    try:
        pages = int(sys.argv[2])
    except ValueError:
        raise ValueError("Le nombre de pages doit être un entier.")

    root = Path(sys.argv[3]).resolve()

    if pages < 1:
        raise ValueError("Le nombre de pages doit être supérieur ou égal à 1.")

    if dataset not in {"books", "gaaraas"}:
        raise ValueError("Dataset invalide : books ou gaaraas.")

    state_file = root / "data" / "temp" / "dataforge_scraping_job.json"

    write_state(
        state_file,
        dataset=dataset,
        status="starting",
        stage="initialisation",
        pages=pages,
        current_page=0,
        total_pages=pages,
        message=f"Démarrage du scraping {dataset} — {pages} page(s).",
    )

    try:
        if dataset == "books":
            run_books(root, pages, state_file)
        else:
            run_gaaraas(root, pages, state_file)

    except Exception as exc:
        write_state(
            state_file,
            dataset=dataset,
            status="failed",
            stage="error",
            pages=pages,
            error=str(exc),
            message=f"Le scraping {dataset} a échoué.",
        )
        raise


if __name__ == "__main__":
    main()
