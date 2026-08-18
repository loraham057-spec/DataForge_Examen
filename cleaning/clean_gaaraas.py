import pandas as pd
import os


INPUT_FILE = "data/cleaned/gaaraas_full.csv"
OUTPUT_FILE = "data/cleaned/gaaraas_clean.csv"


def clean_text(value):

    if pd.isna(value):
        return ""

    return " ".join(
        str(value).split()
    ).strip()


def clean_brand(value):

    value = clean_text(value)

    corrections = {
        "Mercedes‒Benz": "Mercedes-Benz",
        "Mercedes Benz": "Mercedes-Benz"
    }

    return corrections.get(
        value,
        value
    )


def clean_price(value):

    if pd.isna(value):
        return None

    try:

        return int(
            float(value)
        )

    except (ValueError, TypeError):

        return None


def clean_integer(value):

    if pd.isna(value):
        return None

    try:

        return int(
            float(value)
        )

    except (ValueError, TypeError):

        return None


def main():

    print("=" * 70)
    print("🚗 NETTOYAGE FINAL — GAARAAS")
    print("=" * 70)

    # ---------------------------------------------------------
    # Lecture
    # ---------------------------------------------------------

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig"
    )

    print(
        f"\n📂 Lignes initiales : {len(df)}"
    )

    # ---------------------------------------------------------
    # Nettoyage texte
    # ---------------------------------------------------------

    print("\n🧹 Nettoyage des textes...")

    text_columns = [
        "brand",
        "model",
        "gearbox",
        "region",
        "listing_url"
    ]

    for column in text_columns:

        df[column] = df[column].apply(
            clean_text
        )

    # ---------------------------------------------------------
    # Marques
    # ---------------------------------------------------------

    print("🏷️ Normalisation des marques...")

    df["brand"] = df[
        "brand"
    ].apply(
        clean_brand
    )

    # ---------------------------------------------------------
    # Variables numériques
    # ---------------------------------------------------------

    print("💰 Nettoyage des prix...")

    df["price"] = df[
        "price"
    ].apply(
        clean_price
    )

    print("🚗 Nettoyage des kilométrages...")

    df["mileage"] = df[
        "mileage"
    ].apply(
        clean_integer
    )

    print("📅 Nettoyage des années...")

    df["year"] = df[
        "year"
    ].apply(
        clean_integer
    )

    # ---------------------------------------------------------
    # Identifiants techniques
    # ---------------------------------------------------------

    df["page"] = pd.to_numeric(
        df["page"],
        errors="coerce"
    ).astype("Int64")

    df["position_page"] = pd.to_numeric(
        df["position_page"],
        errors="coerce"
    ).astype("Int64")

    # ---------------------------------------------------------
    # Contrôle URL
    # ---------------------------------------------------------

    print("\n🔎 Contrôle des URLs...")

    duplicate_urls = df[
        df.duplicated(
            subset=["listing_url"],
            keep=False
        )
    ]

    print(
        f"URLs dupliquées : "
        f"{len(duplicate_urls)}"
    )

    # ---------------------------------------------------------
    # Colonnes finales
    # ---------------------------------------------------------

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
        "listing_url"
    ]

    df = df[columns]

    # ---------------------------------------------------------
    # Contrôle qualité
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("🔍 CONTRÔLE QUALITÉ")
    print("=" * 70)

    print(
        f"\nNombre de lignes : {len(df)}"
    )

    print(
        f"Nombre de colonnes : {len(df.columns)}"
    )

    print("\nValeurs manquantes :")

    print(
        df.isna().sum()
    )

    # ---------------------------------------------------------
    # Statistiques
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("📊 STATISTIQUES GAARAAS")
    print("=" * 70)

    print(
        f"\nPrix moyen : "
        f"{df['price'].mean():,.0f} CFA"
    )

    print(
        f"Prix minimum : "
        f"{df['price'].min():,.0f} CFA"
    )

    print(
        f"Prix maximum : "
        f"{df['price'].max():,.0f} CFA"
    )

    print(
        f"\nKilométrage moyen : "
        f"{df['mileage'].mean():,.0f} km"
    )

    print(
        f"Année moyenne : "
        f"{df['year'].mean():.0f}"
    )

    print(
        f"\nNombre de marques : "
        f"{df['brand'].nunique()}"
    )

    print(
        f"Nombre de modèles : "
        f"{df['model'].nunique()}"
    )

    print("\nBoîtes de vitesses :")

    print(
        df["gearbox"].value_counts()
    )

    print("\nTop 10 marques :")

    print(
        df["brand"]
        .value_counts()
        .head(10)
    )

    # ---------------------------------------------------------
    # Sauvegarde
    # ---------------------------------------------------------

    os.makedirs(
        "data/cleaned",
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 70)
    print("✅ NETTOYAGE GAARAAS TERMINÉ")
    print("=" * 70)

    print(
        f"\n📄 Fichier : {OUTPUT_FILE}"
    )

    print(
        f"📚 Annonces conservées : {len(df)}"
    )

    print(
        f"📊 Colonnes : {len(df.columns)}"
    )

    print("\nAperçu :")

    print(
        df.head(10).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()