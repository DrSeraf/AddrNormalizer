import pandas as pd
from ..clean.text_normalize import norm_text
from ..synth.assemble import assemble_addr_norm
from .reader import safe_get
from ..parse.zipcode import normalize_zip
from ..parse.country import normalize_country

def _combine_street(street_norm: pd.Series, house_number: pd.Series) -> pd.Series:
    """Склеивает 'улица + дом' в один столбец (если один пуст — возвращает другой)."""
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
    addr-only  -> вернуть исходные колонки + country_norm + addr_norm
    extended   -> вернуть нормализованные: street, locality_norm, district_norm, region_norm, zip_norm, country_norm, addr_norm
    """
    # before (для логов)
    country_b  = safe_get(df, "country")
    region_b   = safe_get(df, "region")
    district_b = safe_get(df, "district")
    locality_b = safe_get(df, "locality")
    street_b   = safe_get(df, "street")
    zipc_b     = safe_get(df, "zip")

    # after (базовая нормализация текста)
    region   = region_b.map(norm_text)
    district = district_b.map(norm_text)
    locality = locality_b.map(norm_text)
    street   = street_b.map(norm_text)
    zipc     = zipc_b.map(norm_text)

    # ZIP normalize (и подсказка страны)
    zip_results = [normalize_zip(None if not c else c, z) for c, z in zip(country_b.map(norm_text), zipc)]
    zip_norm = pd.Series([zr.zip_norm for zr in zip_results], dtype="string")
    zip_inferred_iso2 = [zr.country_inferred for zr in zip_results]

    # COUNTRY normalize (используем подсказку ZIP при пустом/непонятном поле)
    country_res = [normalize_country(c, zi) for c, zi in zip(country_b.map(norm_text), zip_inferred_iso2)]
    country     = pd.Series([cr.name for cr in country_res], dtype="string")
    # iso2 мы пока не выводим, но держим на будущее
    # country_iso = [cr.iso2 for cr in country_res]

    # Дом пока не выделяем
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
        "street":   (street_b,   street_norm),
        "locality": (locality_b, locality),
        "district": (district_b, district),
        "region":   (region_b,   region),
        "country":  (country_b,  country),
        "zip":      (zipc_b,     zip_norm),
    }

    if output_mode == "addr-only":
        out = df.copy()  # исходные колонки пользователя
        out["country_norm"] = country
        out["addr_norm"] = addr_norm
        return out, changes

    # extended: нужный порядок + country_norm
    street_combined = _combine_street(street_norm, house_number)
    out = pd.DataFrame({
        "street":        street_combined,
        "locality_norm": locality,
        "district_norm": district,
        "region_norm":   region,
        "zip_norm":      zip_norm,
        "country_norm":  country,
        "addr_norm":     addr_norm,
    })
    return out, changes

def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8")
