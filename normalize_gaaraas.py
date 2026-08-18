from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "data" / "cleaned" / "gaaraas_full.csv"

GENERIC_NAMES = {
    "",
    "notre histoire",
    "notre histoire...",
    "notre histoire…",
}

def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def from_listing_url(url):
    """
    Exemple :
    annonce-peugeot-207-dakar-dakar-908
    -> Peugeot / 207

    Le slug est utilisé uniquement pour corriger les titres génériques.
    """
    url = normalize_text(url).lower()
    match = re.search(
        r"/vehicle_listings/annonce-([^/]+)$",
        url,
    )
    if not match:
        return "", ""

    slug = match.group(1)

    # Retirer l'identifiant final.
    slug = re.sub(r"-\d+$", "", slug)

    parts = [p for p in slug.split("-") if p]

    if not parts:
        return "", ""

    # Les deux derniers segments correspondent normalement
    # à ville / ville. On les retire.
    if len(parts) >= 2:
        parts = parts[:-2]

    if not parts:
        return "", ""

    # Le premier segment est la marque.
    brand = parts[0].title()

    # Le reste correspond au modèle.
    model = " ".join(parts[1:]).title()

    # Marques composées fréquentes.
    if len(parts) >= 2:
        two = f"{parts[0]} {parts[1]}".lower()
        if two in {
            "land rover",
            "alfa romeo",
            "mercedes benz",
            "aston martin",
            "rolls royce",
        }:
            brand = f"{parts[0]} {parts[1]}".title()
            model = " ".join(parts[2:]).title()

    return brand, model


def main():
    print("=" * 70)
    print("DATAFORGE - NORMALISATION GAARAAS")
    print("=" * 70)

    if not CSV.exists():
        raise FileNotFoundError(f"CSV introuvable : {CSV}")

    df = pd.read_csv(CSV)

    if "listing_url" not in df.columns:
        raise ValueError("La colonne listing_url est absente.")

    corrected = 0

    for index, row in df.iterrows():
        brand = normalize_text(row.get("brand", ""))
        model = normalize_text(row.get("model", ""))

        if brand.lower() in GENERIC_NAMES:
            new_brand, new_model = from_listing_url(
                row["listing_url"]
            )

            if new_brand:
                df.at[index, "brand"] = new_brand

                # Le scraper peut avoir placé l'année dans model
                # quand le titre est générique.
                if (
                    not model
                    or re.fullmatch(r"\d{4}(\.0)?", model)
                ):
                    df.at[index, "model"] = new_model
                else:
                    df.at[index, "model"] = new_model

                corrected += 1

    df.to_csv(
        CSV,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Lignes corrigées : {corrected}")
    print(f"Total lignes     : {len(df)}")
    print()
    print(
        df[
            [
                "brand",
                "model",
                "year",
                "price",
                "listing_url",
            ]
        ].head(10).to_string(index=False)
    )

    print()
    print("CSV GAARAAS CORRIGÉ.")


if __name__ == "__main__":
    main()
