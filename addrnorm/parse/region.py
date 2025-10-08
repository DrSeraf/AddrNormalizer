from __future__ import annotations
import re
from typing import Optional
from ..rules.registry import get_region_aliases, get_country_index

def _norm_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _key(s: str) -> str:
    s = s.lower().strip()
    # убираем пробелы/точки/дефисы/подчёркивания и прочее не-алфанум
    return "".join(ch for ch in s if ch.isalnum())

def _iso2_from_country_name(name: str | None) -> str | None:
    if not name:
        return None
    idx = get_country_index()  # ISO2 -> Canonical
    name_l = name.strip().lower()
    for iso2, canon in idx.items():
        if name_l == canon.lower():
            return iso2
    return None

def normalize_region(region_raw: Optional[str], country_iso2: Optional[str], country_name: Optional[str]) -> str:
    """
    Если страна США — разворачиваем алиасы штатов в полные имена.
    Иначе — возвращаем аккуратно очищенное значение.
    """
    region_raw = _norm_text(region_raw)
    if not region_raw:
        return ""

    iso = (country_iso2 or "").strip().upper()
    if not iso:
        # восстановим iso2 из названия страны, если оно каноническое
        iso = (_iso2_from_country_name(country_name) or "").upper()

    if iso == "US":
        aliases = get_region_aliases("US")
        val = aliases.get(_key(region_raw))
        if val:
            return val
        return region_raw

    # остальные страны — только чистка
    return region_raw
