from __future__ import annotations
from dataclasses import dataclass
from ..rules.registry import get_country_index, get_country_aliases

def _clean(s: str | None) -> str:
    if not s:
        return ""
    return str(s).strip().lower()

@dataclass
class CountryResult:
    name: str
    iso2: str | None
    source: str

_ISO3_TO_ISO2 = {
    "usa": "US", "rus": "RU", "deu": "DE", "esp": "ES", "ita": "IT", "nld": "NL",
    "fra": "FR", "gbr": "GB", "can": "CA", "chn": "CN", "jpn": "JP", "ind": "IN",
    "aus": "AU", "bra": "BR", "mex": "MX", "pol": "PL", "prt": "PT", "bel": "BE",
    "aut": "AT", "swe": "SE", "nor": "NO", "dnk": "DK", "fin": "FI", "irl": "IE", "che": "CH",
}

def _iso2_from_text(txt: str) -> str | None:
    t = txt.upper()
    if len(t) == 2:
        return t
    if len(t) == 3:
        return _ISO3_TO_ISO2.get(t.lower())
    return None

def normalize_country(country_raw: str | None, zip_inferred_iso2: str | None = None) -> CountryResult:
    idx = get_country_index()
    aliases = get_country_aliases()
    raw = _clean(country_raw)

    # 1) прямое совпадение с каноном
    if raw:
        for iso2, canon in idx.items():
            if raw == canon.lower():
                return CountryResult(name=canon, iso2=iso2, source="input")

    # 2) алиасы
    if raw and raw in aliases:
        canon = aliases[raw]
        iso2 = next((k for k, v in idx.items() if v.lower() == canon.lower()), None)
        return CountryResult(name=canon, iso2=iso2, source="alias")

    # 3) ISO2/ISO3
    if raw:
        iso2 = _iso2_from_text(raw)
        if iso2 and iso2 in idx:
            return CountryResult(name=idx[iso2], iso2=iso2, source="iso")

    # 4) ZIP inference
    if (not raw) and zip_inferred_iso2 and zip_inferred_iso2.upper() in idx:
        iso2 = zip_inferred_iso2.upper()
        return CountryResult(name=idx[iso2], iso2=iso2, source="inferred_zip")

    return CountryResult(name="", iso2=None, source="unknown")
