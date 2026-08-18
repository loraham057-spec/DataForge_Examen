import pandas as pd
import os


INPUT_FILE = "data/cleaned/books_full.csv"
OUTPUT_FILE = "data/cleaned/books_clean.csv"


RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}


def clean_text(value):

    if pd.isna(value):
        return ""

    return " ".join(
        str(value).split()
    ).strip()


def clean_price(value):

    if pd.isna(value):
        return None

    value = str(value)

    value = (
        value
        .replace("£", "")
        .replace(",", "")
        .strip()
    )

    try:
        return float(value)

    except ValueError:
        return None


def clean_rating(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    return RATING_MAP.get(value)


def clean_reviews(value):

    if pd.isna(value):
        return 0

    try:
        return int(float(value))

    except ValueError:
        return 0


def clean_tax(value):

    return clean_price(value)


def clean_availability(value):

    if pd.isna(value):
        return ""

    value = str(value).strip()

    if "In stock" in value:
        return "In stock"

    if "Out of stock" in value:
        return "Out of stock"

    return value


def main():

    print("=" * 70)
    print("📚 NETTOYAGE FINAL — BOOKS TO SCRAPE")
    print("=" * 70)

    # =========================================================
    # 1. Lecture
    # =========================================================

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig"
    )

    print(
        f"\n📂 Lignes initiales : {len(df)}"
    )

    print(
        f"📊 Colonnes initiales : {len(df.columns)}"
    )

    # Compatibilité avec d'anciens exports : le nombre de produits
    # par page est une variable exigée par le sujet.
    if "products_count" not in df.columns:
        df["products_count"] = (
            df.groupby("page")["position_page"]
            .transform("max")
            .astype("Int64")
        )

    # =========================================================
    # 2. Nettoyage des textes
    # =========================================================

    print("\n🧹 Nettoyage des textes...")

    text_columns = [
        "title",
        "availability",
        "description",
        "category",
        "book_url"
    ]

    for column in text_columns:

        df[column] = df[column].apply(
            clean_text
        )

    # =========================================================
    # 3. Nettoyage prix
    # =========================================================

    print("💰 Nettoyage des prix...")

    df["price"] = df["price"].apply(
        clean_price
    )

    # =========================================================
    # 4. Nettoyage taxe
    # =========================================================

    print("💰 Nettoyage des taxes...")

    df["tax"] = df["tax"].apply(
        clean_tax
    )

    # =========================================================
    # 5. Nettoyage rating
    # =========================================================

    print("⭐ Conversion des notes...")

    df["rating"] = df["rating"].apply(
        clean_rating
    )

    # =========================================================
    # 6. Reviews
    # =========================================================

    print("📝 Conversion des reviews...")

    df["reviews"] = df["reviews"].apply(
        clean_reviews
    )

    # =========================================================
    # 7. Disponibilité
    # =========================================================

    print("📦 Normalisation de la disponibilité...")

    df["availability"] = df[
        "availability"
    ].apply(
        clean_availability
    )

    # =========================================================
    # 8. Types numériques
    # =========================================================

    df["page"] = pd.to_numeric(
        df["page"],
        errors="coerce"
    ).astype("Int64")

    df["position_page"] = pd.to_numeric(
        df["position_page"],
        errors="coerce"
    ).astype("Int64")

    df["products_count"] = pd.to_numeric(
        df["products_count"],
        errors="coerce"
    ).astype("Int64")

    # =========================================================
    # 9. Contrôle des doublons
    # =========================================================

    print("\n🔎 Contrôle des doublons...")

    duplicate_urls = df[
        df.duplicated(
            subset=["book_url"],
            keep=False
        )
    ]

    if len(duplicate_urls) == 0:

        print(
            "   ✓ Aucun doublon détecté sur book_url."
        )

    else:

        print(
            f"   ⚠️ {len(duplicate_urls)} lignes "
            "concernées par des URLs répétées."
        )

    # =========================================================
    # 10. Vérification des valeurs manquantes
    # =========================================================

    print("\n🔍 Valeurs manquantes :")

    missing = df.isna().sum()

    print(missing)

    # =========================================================
    # 11. Contrôles métier
    # =========================================================

    print("\n📊 CONTRÔLES MÉTIER")

    print(
        f"Nombre de livres : {len(df)}"
    )

    print(
        f"Prix moyen : £{df['price'].mean():.2f}"
    )

    print(
        f"Prix minimum : £{df['price'].min():.2f}"
    )

    print(
        f"Prix maximum : £{df['price'].max():.2f}"
    )

    print(
        f"Note moyenne : "
        f"{df['rating'].mean():.2f}/5"
    )

    print(
        f"Reviews totales : "
        f"{df['reviews'].sum()}"
    )

    print(
        f"Taxe moyenne : "
        f"£{df['tax'].mean():.2f}"
    )

    print("\n📚 Livres par note :")

    print(
        df["rating"]
        .value_counts()
        .sort_index()
    )

    print("\n📚 Livres par catégorie :")

    print(
        df["category"]
        .value_counts()
        .head(10)
    )

    # =========================================================
    # 12. Ordre des colonnes
    # =========================================================

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
        "book_url"
    ]

    df = df[columns]

    # =========================================================
    # 13. Sauvegarde
    # =========================================================

    os.makedirs(
        "data/cleaned",
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # =========================================================
    # 14. Contrôle final
    # =========================================================

    print("\n" + "=" * 70)
    print("✅ NETTOYAGE FINAL TERMINÉ")
    print("=" * 70)

    print(
        f"\n📄 Fichier : {OUTPUT_FILE}"
    )

    print(
        f"📚 Nombre de lignes : {len(df)}"
    )

    print(
        f"📊 Nombre de colonnes : {len(df.columns)}"
    )

    print("\nColonnes finales :")

    for column in df.columns:

        print(
            f"   ✓ {column}"
        )

    print("\nAperçu :")

    print(
        df.head(10).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()