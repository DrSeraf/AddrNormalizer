import pandas as pd
from ..clean.text_normalize import norm_text
from ..synth.assemble import assemble_addr_norm
from .reader import safe_get
from ..parse.zipcode import normalize_zip
from ..parse.country import normalize_country
from ..parse.region import normalize_region
from ..parse.locality import normalize_locality
from ..parse.street import normalize_street
from ..libpostal.client import LibPostalClient
from ..libpostal.postprocess import (
    pick_street, pick_locality, pick_region, pick_postcode, pick_country
)

def _combine_street(street_norm: pd.Series, house_number: pd.Series) -> pd.Series:
    combined = []
    for s, h in zip(street_norm.fillna(""), house_number.fillna("")):
        s = str(s).strip()
        h = str(h).strip()
        combined.append(f"{s} {h}".strip() if s and h else (s or h))
    return pd.Series(combined, dtype="string")

def _apply_libpostal_row(addr_norm: str, lp: LibPostalClient):
    try:
        comps = lp.parse(addr_norm)
        return comps
    except Exception:
        return []

def process_dataframe(df: pd.DataFrame, output_mode: str = "addr-only",
                      use_libpostal: bool = False, libpostal_url: str = "http://localhost:8080"):
    # before (для логов)
    country_b  = safe_get(df, "country")
    region_b   = safe_get(df, "region")
    district_b = safe_get(df, "district")
    locality_b = safe_get(df, "locality")
    street_b   = safe_get(df, "street")
    zipc_b     = safe_get(df, "zip")

    # базовая чистка для некоторых полей
    district = district_b.map(norm_text)
    zipc     = zipc_b.map(norm_text)

    # ZIP
    zip_results = [normalize_zip(None if not c else c, z) for c, z in zip(country_b.map(norm_text), zipc)]
    zip_norm = pd.Series([zr.zip_norm for zr in zip_results], dtype="string")
    zip_inferred_iso2 = [zr.country_inferred for zr in zip_results]

    # COUNTRY
    country_res = [normalize_country(c, zi) for c, zi in zip(country_b.map(norm_text), zip_inferred_iso2)]
    country     = pd.Series([cr.name for cr in country_res], dtype="string")
    country_iso = [cr.iso2 for cr in country_res]

    # REGION
    region_norm_list = [normalize_region(r, iso2, cname) for r, iso2, cname in zip(region_b, country_iso, country)]
    region = pd.Series(region_norm_list, dtype="string")

    # LOCALITY
    locality_norm_list = [normalize_locality(loc, iso2, cname) for loc, iso2, cname in zip(locality_b, country_iso, country)]
    locality = pd.Series(locality_norm_list, dtype="string")

    # STREET
    street_norm_list = [normalize_street(s) for s in street_b]
    street = pd.Series(street_norm_list, dtype="string")

    # дом пока не выделяем
    house_number = pd.Series([""] * len(df), dtype="string")

    # addr_norm из наших нормализованных компонент
    addr_norm = [
        assemble_addr_norm(
            country[i], region[i], district[i], locality[i],
            street[i], house_number[i], zip_norm[i]
        )
        for i in range(len(df))
    ]
    addr_norm = pd.Series(addr_norm, dtype="string")

    # --------- ПОСЛЕ очистки: прогон через libpostal (опционально) ----------
    if use_libpostal:
        lp = LibPostalClient(base_url=libpostal_url, timeout=5.0, retries=1)

        # применяем пост-обработку построчно
        street_lp, locality_lp, region_lp, zip_lp, country_lp = [], [], [], [], []
        for a in addr_norm.fillna(""):
            comps = _apply_libpostal_row(a, lp)

            # STREET: road + housenumber (если есть), иначе оставляем как было
            s2 = pick_street(comps)
            street_lp.append(s2 if s2 else "")

            # LOCALITY: city/town/village/suburb/...
            loc2 = pick_locality(comps)
            locality_lp.append(loc2 if loc2 else "")

            # REGION: state/region/province
            reg2 = pick_region(comps)
            region_lp.append(reg2 if reg2 else "")

            # ZIP: postcode
            zp2 = pick_postcode(comps)
            zip_lp.append(zp2 if zp2 else "")

            # COUNTRY: country name/code
            ctry2 = pick_country(comps)
            country_lp.append(ctry2 if ctry2 else "")

        # обновляем поля «мягко»: если libpostal дал значение — используем, иначе оставляем прежнее
        # street: заменяем, если libpostal дал улицу (он уже включает дом)
        street = pd.Series([street_lp[i] or street.iloc[i] for i in range(len(df))], dtype="string")

        # locality/region: если libpostal дал — нормализуем через наши функции ещё раз (чтобы титл-кейс и штаты США)
        locality = pd.Series(
            [normalize_locality(locality_lp[i], country_iso[i], country.iloc[i]) or locality.iloc[i] for i in range(len(df))],
            dtype="string"
        )
        region = pd.Series(
            [normalize_region(region_lp[i], country_iso[i], country.iloc[i]) or region.iloc[i] for i in range(len(df))],
            dtype="string"
        )

        # zip: если дал — прогоняем через нашу normalize_zip (чтобы слитная форма)
        zip_norm = pd.Series(
            [normalize_zip(country_iso[i], zip_lp[i]).zip_norm if zip_lp[i] else zip_norm.iloc[i] for i in range(len(df))],
            dtype="string"
        )

        # country: если дал — нормализуем через нашу normalize_country (канон-имя)
        country_after = []
        country_iso_after = []
        for i in range(len(df)):
            if country_lp[i]:
                cres = normalize_country(country_lp[i], None)
                name = cres.name or country.iloc[i]
                iso2 = cres.iso2 if cres.iso2 else (country_iso[i] if country_iso[i] else None)
                country_after.append(name)
                country_iso_after.append(iso2)
            else:
                country_after.append(country.iloc[i])
                country_iso_after.append(country_iso[i] if country_iso[i] else None)
        country = pd.Series(country_after, dtype="string")
        country_iso = country_iso_after

        # пересоберём addr_norm после libpostal-уточнений
        addr_norm = pd.Series([
            assemble_addr_norm(
                country[i], region[i], district[i], locality[i],
                street[i], house_number[i], zip_norm[i]
            )
            for i in range(len(df))
        ], dtype="string")

    # логи
    changes = {
        "street":   (street_b,   street),
        "locality": (locality_b, locality),
        "district": (district_b, district),
        "region":   (region_b,   region),
        "country":  (country_b,  country),
        "zip":      (zipc_b,     zip_norm),
    }

    if output_mode == "addr-only":
        out = df.copy()
        out["country_norm"] = country
        out["addr_norm"] = addr_norm
        return out, changes

    # extended
    street_combined = _combine_street(street, house_number)  # сейчас house_number пуст, но логика на будущее
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
