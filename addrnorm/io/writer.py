import pandas as pd
from ..clean.text_normalize import norm_text
from ..synth.assemble import assemble_addr_norm
from .reader import safe_get

EXTENDED_COLS = ["zip_norm","region_norm","district_norm","locality_norm","street_norm","house_number","addr_norm"]

def process_dataframe(df: pd.DataFrame, output_mode: str = "addr-only"):
    # before
    country_b = safe_get(df,"country")
    region_b = safe_get(df,"region")
    district_b = safe_get(df,"district")
    locality_b = safe_get(df,"locality")
    street_b = safe_get(df,"street")
    zipc_b = safe_get(df,"zip")

    # after (v0 — простая нормализация)
    country = country_b.map(norm_text)
    region = region_b.map(norm_text)
    district = district_b.map(norm_text)
    locality = locality_b.map(norm_text)
    street = street_b.map(norm_text)
    zipc = zipc_b.map(norm_text)

    # Пока без парсинга дома
    street_norm = street
    house_number = pd.Series([""]*len(df), dtype="string")
    zip_norm = zipc

    addr_norm = [
        assemble_addr_norm(country[i], region[i], district[i], locality[i], street_norm[i], house_number[i], zip_norm[i])
        for i in range(len(df))
    ]
    addr_norm = pd.Series(addr_norm, dtype="string")

    if output_mode == "addr-only":
        out = pd.DataFrame({"addr_norm": addr_norm})
    else:
        out = pd.DataFrame({
            "zip_norm": zip_norm,
            "region_norm": region,
            "district_norm": district,
            "locality_norm": locality,
            "street_norm": street_norm,
            "house_number": house_number,
            "addr_norm": addr_norm,
        })

    # «трасса» для логов (только ключевые поля)
    changes = {
        "zip": (zipc_b, zip_norm),
        "region": (region_b, region),
        "district": (district_b, district),
        "locality": (locality_b, locality),
        "street": (street_b, street_norm),
    }
    return out, changes

def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8")
