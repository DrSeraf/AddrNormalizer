import pandas as pd
from ..clean.text_normalize import norm_text
from ..synth.assemble import assemble_addr_norm
from .reader import safe_get
from ..parse.zipcode import normalize_zip

def _combine_street(street_norm: pd.Series, house_number: pd.Series) -> pd.Series:
    """
    Склеивает 'улица + дом' в один столбец.
    Если один из компонентов пуст — возвращает другой.
    """
    combined = []
    for s, h in zip(street_norm.fillna(""), house_number.fillna("")):
        s = str(s).strip()
        h = str(h).strip()
        if s and h:
            combined.append(f"{s} {h}")
        else:
            combined.append(s or h)
    return pd.Series(combined, dtype="string")

def process_dataframe(df: pd.DataFrame, output_mode: str = "addr-only"):
    """
    addr-only  -> вернуть исходные колонки + добавить addr_norm
    extended   -> вернуть нормализованные: street(улица+дом), locality_norm, district_norm, region_norm, zip_norm, addr_norm
    """
    # before (для логов изменений)
    country_b  = safe_get(df, "country")
    region_b   = safe_get(df, "region")
    district_b = safe_get(df, "district")
    locality_b = safe_get(df, "locality")
    street_b   = safe_get(df, "street")
    zipc_b     = safe_get(df, "zip")

    # after (v0 — базовая нормализация текста)
    country  = country_b.map(norm_text)
    region   = region_b.map(norm_text)
    district = district_b.map(norm_text)
    locality = locality_b.map(norm_text)
    street   = street_b.map(norm_text)
    zipc     = zipc_b.map(norm_text)

    # ZIP: универсальная нормализация/валидация
    zip_norm_list = []
    for c, z in zip(country.tolist(), zipc.tolist()):
        zr = normalize_zip(c if c else None, z)
        zip_norm_list.append(zr.zip_norm)
    zip_norm = pd.Series(zip_norm_list, dtype="string")

    # Дом пока не выделяем — просто пусто (логика готова на будущее)
    house_number = pd.Series([""] * len(df), dtype="string")
    street_norm  = street

    # addr_norm из нормализованных компонент
    addr_norm = [
        assemble_addr_norm(
            country[i], region[i], district[i], locality[i],
            street_norm[i], house_number[i], zip_norm[i]
        )
        for i in range(len(df))
    ]
    addr_norm = pd.Series(addr_norm, dtype="string")

    # трасса изменений для логов
    changes = {
        "zip":      (zipc_b,     zip_norm),
        "region":   (region_b,   region),
        "district": (district_b, district),
        "locality": (locality_b, locality),
        "street":   (street_b,   street_norm),
    }

    if output_mode == "addr-only":
        out = df.copy()
        out["addr_norm"] = addr_norm
        return out, changes

    # extended: один столбец street (улица + дом), нужный порядок, без house_number
    street_combined = _combine_street(street_norm, house_number)
    out = pd.DataFrame({
        "street":        street_combined,
        "locality_norm": locality,
        "district_norm": district,
        "region_norm":   region,
        "zip_norm":      zip_norm,
        "addr_norm":     addr_norm,
    })
    return out, changes

def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8")
