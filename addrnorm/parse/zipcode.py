from __future__ import annotations
import re
from dataclasses import dataclass
from ..rules.registry import get_zip_patterns

@dataclass
class ZipResult:
    zip_norm: str
    valid: bool
    country_inferred: str | None
    style: str | None

_ALNUM_ONLY = re.compile(r"[A-Za-z0-9]+")

def _clean_zip(s: str) -> str:
    if not s:
        return ""
    return "".join(_ALNUM_ONLY.findall(str(s))).upper()

def _match_against(patterns, s: str) -> bool:
    for p in patterns:
        if re.match(p, s, flags=re.IGNORECASE):
            return True
    return False

def normalize_zip(country: str | None, zip_raw: str | None) -> ZipResult:
    z_raw = (zip_raw or "").strip()
    if not z_raw:
        return ZipResult("", False, None, None)

    cleaned = _clean_zip(z_raw)
    zp = get_zip_patterns()

    if country:
        entry = zp.get(country.upper())
        if entry:
            pats = entry.get("patterns") or []
            style = entry.get("style")
            valid = _match_against(pats, z_raw) or _match_against(pats, cleaned)
            return ZipResult(cleaned, bool(valid), None, style)
        return ZipResult(cleaned, False, None, None)

    # infer
    for iso2, entry in zp.items():
        pats = entry.get("patterns") or []
        if _match_against(pats, z_raw) or _match_against(pats, cleaned):
            return ZipResult(cleaned, True, iso2, entry.get("style"))

    return ZipResult(cleaned, False, None, None)
