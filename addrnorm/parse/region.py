from __future__ import annotations
import re
from typing import Optional
from ..rules.registry import get_region_aliases

def _norm_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _key(s: str) -> str:
    s = s.lower().strip()
    return "".join(ch for ch in s if ch.isalnum())  # убираем пробелы/точки/дефисы/подчёркивания

def normalize_region(region_raw: Optional[str], country_iso2: Optional[str], country_name: Optional[str]) -> str:
    region_raw = _norm_text(region_raw)
    if not region_raw:
        return ""

    iso = (country_iso2 or "").upper()
    if not iso and country_name and country_name.strip().lower() == "united states":
        iso = "US"

    if iso == "US":
        aliases = get_region_aliases("US")
        val = aliases.get(_key(region_raw))
        if val:
            return val
        return region_raw

    # Остальные страны пока без расширенной нормализации
    return region_raw
