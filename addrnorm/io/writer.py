# writer.py
import pandas as pd
from ..clean.text_normalize import norm_text
from ..synth.assemble import assemble_addr_norm
from .reader import safe_get

EXTENDED_COLS = ["zip_norm","region_norm","district_norm","locality_norm","street_norm","house_number","addr_norm"]

def process_dataframe(df: pd.DataFrame, output_mode: str = "addr-only") -> pd.DataFrame:
    # v0: простая нормализация без сложных правил/словарей
    country = safe_get(df,"country").map(norm_text)
    region = safe_get(df,"region").map(norm_text)
    district = safe_get(df,"district").map(norm_text)
    locality = safe_get(df,"locality").map(norm_text)
    street = safe_get(df,"street").map(norm_text)
    zipc = safe_get(df,"zip").map(norm_text)

    # Пока без парсинга дома: house_number пуст, street_norm = street
    street_norm = street
    house_number = pd.Series([""]*len(df), dtype="string")

    # zip_norm = zip (валидацию добавим позже)
    zip_norm = zipc

    addr_norm = [
        assemble_addr_norm(country[i], region[i], district[i], locality[i], street_norm[i], house_number[i], zip_norm[i])
        for i in range(len(df))
    ]
    addr_norm = pd.Series(addr_norm, dtype="string")

    if output_mode == "addr-only":
        return pd.DataFrame({"addr_norm": addr_norm})
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
        return out

def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8")
