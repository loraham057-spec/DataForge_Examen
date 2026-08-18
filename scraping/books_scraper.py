from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com"
CATALOGUE_URL = BASE_URL + "/catalogue/page-{}.html"

START_PAGE = 1
END_PAGE = 1

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "cleaned"
TEMP_DIR = ROOT / "data" / "temp"
OUTPUT_FILE = OUTPUT_DIR / "books_full.csv"
STATE_FILE = TEMP_DIR / "dataforge_scraping_job.json"

TIMEOUT = (10, 25)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def update_state(**values):
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    state.update(values)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def get_soup(session, url):
    response = session.get(
        url,
        timeout=TIMEOUT,
        allow_redirects=True,
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def get_rating(article):
    node = article.select_one("p.star-rating")
    if not node:
        return ""
    for item in node.get("class", []):
        if item != "star-rating":
            return item
    return ""


def scrape_book_details(session, book_url):
    details = {
        "description": "",
        "category": "",
        "tax": "",
        "reviews": "",
    }

    if not book_url:
        return details

    try:
        soup = get_soup(session, book_url)

        description_title = soup.select_one("#product_description")
        if description_title:
            paragraph = description_title.find_next_sibling("p")
            if paragraph:
                details["description"] = clean_text(
                    paragraph.get_text(" ", strip=True)
                )

        breadcrumbs = soup.select("ul.breadcrumb li")
        if len(breadcrumbs) >= 3:
            details["category"] = clean_text(
                breadcrumbs[2].get_text(" ", strip=True)
            )

        for row in soup.select("table.table-striped tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue

            field = clean_text(th.get_text(" ", strip=True))
            value = clean_text(td.get_text(" ", strip=True))

            if field == "Tax":
                details["tax"] = value
            elif field == "Number of reviews":
                details["reviews"] = value

    except requests.RequestException as exc:
        print(f"      ⚠️ détail inaccessible : {exc}")
    except Exception as exc:
        print(f"      ⚠️ erreur détail : {exc}")

    return details


def scrape_books_page(session, page_number):
    page_url = CATALOGUE_URL.format(page_number)

    print()
    print("=" * 70)
    print(f"📄 PAGE {page_number}")
    print(f"🌐 {page_url}")
    print("=" * 70)

    soup = get_soup(session, page_url)
    articles = soup.select("article.product_pod")

    print(f"📚 {len(articles)} livres")

    rows = []

    for position, article in enumerate(articles, start=1):
        title_link = article.select_one("h3 a")
        if not title_link:
            continue

        title = clean_text(
            title_link.get("title")
            or title_link.get_text(" ", strip=True)
        )

        price_node = article.select_one("p.price_color")
        availability_node = article.select_one(
            "p.instock.availability"
        )

        price = (
            clean_text(price_node.get_text(" ", strip=True))
            if price_node else ""
        )

        availability = (
            clean_text(
                availability_node.get_text(" ", strip=True)
            )
            if availability_node else ""
        )

        rating = get_rating(article)

        # CORRECTION PRINCIPALE :
        # Le href est relatif à la page catalogue.
        # On utilise donc page_url, pas BASE_URL.
        href = title_link.get("href", "")
        book_url = urljoin(page_url, href)

        print(
            f"   [{position:02d}/{len(articles)}] "
            f"{title[:65]}"
        )

        details = scrape_book_details(session, book_url)

        rows.append(
            {
                "page": page_number,
                "position_page": position,
                "title": title,
                "price": price,
                "availability": availability,
                "products_count": len(articles),
                "rating": rating,
                "reviews": details["reviews"],
                "description": details["description"],
                "category": details["category"],
                "tax": details["tax"],
                "book_url": book_url,
            }
        )

        time.sleep(0.05)

    return rows


def save_results(rows):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    columns = [
        "page",
        "position_page",
        "title",
        "price",
        "availability",
        "products_count",
        "rating",
        "reviews",
        "description",
        "category",
        "tax",
        "book_url",
    ]

    df = pd.DataFrame(rows)

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    df = df[columns]

    if not df.empty:
        df = df.drop_duplicates(
            subset=["book_url"],
            keep="first",
        )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    return df


def scrape_all_books(start_page=1, end_page=1):
    start_page = int(start_page)
    end_page = int(end_page)

    if start_page < 1:
        raise ValueError("start_page doit être >= 1.")

    if end_page < start_page:
        raise ValueError("end_page doit être >= start_page.")

    total_pages = end_page - start_page + 1
    rows = []
    pages_completed = []

    update_state(
        dataset="books",
        status="running",
        stage="catalogue",
        current_page=0,
        total_pages=total_pages,
        progress=0,
        message=f"Scraping Books : pages {start_page} à {end_page}",
        output=str(OUTPUT_FILE),
        error=None,
    )

    session = create_session()

    try:
        for page in range(start_page, end_page + 1):
            relative_page = page - start_page + 1

            update_state(
                status="running",
                stage="catalogue",
                current_page=relative_page - 1,
                total_pages=total_pages,
                progress=int(((relative_page - 1) / total_pages) * 100),
                message=f"Collecte de la page {page}/{end_page}...",
            )

            try:
                page_rows = scrape_books_page(session, page)
                rows.extend(page_rows)
                pages_completed.append(page)

                progress = int((relative_page / total_pages) * 100)

                update_state(
                    status="running",
                    stage="catalogue",
                    current_page=relative_page,
                    total_pages=total_pages,
                    progress=progress,
                    message=(
                        f"Page {page} terminée : "
                        f"{len(page_rows)} livre(s). "
                        f"Total : {len(rows)}."
                    ),
                )

                print(
                    f"✅ Page {page} terminée : "
                    f"{len(page_rows)} livre(s)"
                )

            except requests.RequestException as exc:
                print(f"❌ Erreur réseau page {page}: {exc}")
                update_state(
                    status="running",
                    stage="catalogue",
                    current_page=relative_page,
                    total_pages=total_pages,
                    progress=int((relative_page / total_pages) * 100),
                    message=f"⚠️ Page {page} en erreur réseau : {exc}",
                )

            except Exception as exc:
                print(f"❌ Erreur page {page}: {exc}")
                update_state(
                    status="running",
                    stage="catalogue",
                    current_page=relative_page,
                    total_pages=total_pages,
                    progress=int((relative_page / total_pages) * 100),
                    message=f"⚠️ Page {page} en erreur : {exc}",
                )

    finally:
        session.close()

    df = save_results(rows)

    update_state(
        dataset="books",
        status="completed",
        stage="finished",
        current_page=total_pages,
        total_pages=total_pages,
        progress=100,
        message=(
            f"Scraping terminé : {len(df):,} livre(s) "
            f"sur {len(pages_completed)} page(s)."
        ),
        output=str(OUTPUT_FILE),
        rows=len(df),
        error=None,
    )

    print()
    print("=" * 70)
    print("✅ SCRAPING BOOKS TERMINÉ")
    print("=" * 70)
    print(f"Pages demandées : {total_pages}")
    print(f"Pages terminées : {len(pages_completed)}")
    print(f"Livres collectés : {len(df)}")
    print(f"CSV : {OUTPUT_FILE}")

    return df


def main():
    # Test direct : UNE SEULE PAGE.
    scrape_all_books(START_PAGE, END_PAGE)


if __name__ == "__main__":
    main()
