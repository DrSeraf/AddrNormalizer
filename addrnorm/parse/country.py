from __future__ import annotations
import os, yaml
from dataclasses import dataclass

# ---------- utils ----------
def _clean(s: str | None) -> str:
    if not s:
        return ""
    return str(s).strip().lower()

@dataclass
class CountryResult:
    name: str            # каноническое полное название (или "")
    iso2: str | None     # "US", "RU", ...
    source: str          # "input", "alias", "iso", "inferred_zip", "unknown"

# Кешы
_ALIAS: dict | None = None
_INDEX: dict | None = None

# Минимальные ISO3→ISO2
_ISO3_TO_ISO2 = {
    "usa": "US", "rus": "RU", "deu": "DE", "esp": "ES", "ita": "IT", "nld": "NL",
    "fra": "FR", "gbr": "GB", "can": "CA", "chn": "CN", "jpn": "JP", "ind": "IN",
    "aus": "AU", "bra": "BR", "mex": "MX", "pol": "PL", "prt": "PT", "bel": "BE",
    "aut": "AT", "swe": "SE", "nor": "NO", "dnk": "DK", "fin": "FI", "irl": "IE", "che": "CH",
}

def _safe_load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    # если это не dict (вдруг список/булеан) — игнорим
    return {}

def _normalize_index_payload(data: dict) -> dict[str, str]:
    """
    Принимает либо {ISO2: Name}, либо {"index": {ISO2: Name}}.
    Фильтрует только строковые пары.
    """
    if "index" in data and isinstance(data["index"], dict):
        data = data["index"]
    out: dict[str, str] = {}
    for k, v in data.items():
        ks = str(k).strip()
        vs = str(v).strip() if v is not None else ""
        if ks and vs:
            out[ks.upper()] = vs
    return out

def _normalize_aliases_payload(data: dict) -> dict[str, str]:
    """
    Ожидает {"aliases": {alias: Canonical, ...}}.
    Все ключи -> lower(), значения — как есть.
    """
    if "aliases" in data and isinstance(data["aliases"], dict):
        data = data["aliases"]
    if not isinstance(data, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in data.items():
        ks = str(k).strip().lower()
        vs = "" if v is None else str(v).strip()
        if ks and vs:
            out[ks] = vs
    return out

def _load_aliases() -> dict[str, str]:
    global _ALIAS
    if _ALIAS is not None:
        return _ALIAS
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "configs", "countries", "_aliases.yaml")
    raw = _safe_load_yaml(path)
    _ALIAS = _normalize_aliases_payload(raw)
    return _ALIAS

def _load_index() -> dict[str, str]:
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "configs", "countries", "_index.yaml")
    raw = _safe_load_yaml(path)
    _INDEX = _normalize_index_payload(raw)
    return _INDEX

def _iso2_from_text(txt: str) -> str | None:
    t = txt.upper()
    if len(t) == 2:
        return t
    if len(t) == 3:
        return _ISO3_TO_ISO2.get(t.lower())
    return None

# ---------- public ----------
def normalize_country(country_raw: str | None, zip_inferred_iso2: str | None = None) -> CountryResult:
    """
    Нормализует страну:
    - прямое совпадение с каноном,
    - алиасы,
    - ISO2/ISO3,
    - если пусто — используем zip_inferred_iso2,
    - иначе unknown.
    """
    idx = _load_index()           # ISO2 -> Canonical
    aliases = _load_aliases()     # alias(lower) -> Canonical

    raw = _clean(country_raw)

    # 1) точное совпадение с канон-именем
    if raw:
        for iso2, canon in idx.items():
            if raw == canon.lower():
                return CountryResult(name=canon, iso2=iso2, source="input")

    # 2) алиасы
    if raw and raw in aliases:
        canon = aliases[raw]
        iso2 = next((k for k, v in idx.items() if v.lower() == canon.lower()), None)
        return CountryResult(name=canon, iso2=iso2, source="alias")

    # 3) ISO2 / ISO3
    if raw:
        iso2 = _iso2_from_text(raw)
        if iso2 and iso2 in idx:
            return CountryResult(name=idx[iso2], iso2=iso2, source="iso")

    # 4) из ZIP (если исходник пуст/непонятен)
    if (not raw) and zip_inferred_iso2 and zip_inferred_iso2.upper() in idx:
        iso2 = zip_inferred_iso2.upper()
        return CountryResult(name=idx[iso2], iso2=iso2, source="inferred_zip")

    # 5) ничего не распознали
    return CountryResult(name="", iso2=None, source="unknown")
