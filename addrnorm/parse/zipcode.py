from __future__ import annotations
import re, os, yaml
from dataclasses import dataclass

_ZIP_CFG_CACHE: dict | None = None

@dataclass
class ZipResult:
    zip_norm: str            # <-- слитная строка A-Z0-9
    valid: bool
    country_inferred: str | None
    style: str | None

def _load_zip_cfg() -> dict:
    global _ZIP_CFG_CACHE
    if _ZIP_CFG_CACHE is not None:
        return _ZIP_CFG_CACHE
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs", "zip_patterns.yaml")
    if not os.path.exists(cfg_path):
        _ZIP_CFG_CACHE = {"countries":{
            "US":{"patterns":[r"^\d{5}$", r"^\d{9}$"], "style":"US"},
            "CA":{"patterns":[r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$"], "style":"CA"},
            "DE":{"patterns":[r"^\d{5}$"], "style":"N5"},
            "RU":{"patterns":[r"^\d{6}$"], "style":"N6"},
        }}
        return _ZIP_CFG_CACHE
    with open(cfg_path, "r", encoding="utf-8") as f:
        _ZIP_CFG_CACHE = yaml.safe_load(f) or {}
    return _ZIP_CFG_CACHE

# ---------- helpers ----------
_ALNUM_ONLY = re.compile(r"[A-Za-z0-9]+")

def _clean_zip(s: str) -> str:
    if not s:
        return ""
    # оставляем только буквы/цифры и приводим к верхнему регистру
    return "".join(_ALNUM_ONLY.findall(str(s))).upper()

def _match_country_against_patterns(s: str, patterns: list[str]) -> bool:
    for p in patterns:
        if re.match(p, s, flags=re.IGNORECASE):
            return True
    return False

def _match_country(z_raw: str, cleaned: str, cfg: dict) -> tuple[str|None, str|None, bool]:
    """
    Пытаемся сопоставить страну:
    1) по 'сырому' вводу (допуская пробел/дефис из паттернов)
    2) по 'слитному' cleaned
    Возвращаем (ISO2, style, matched)
    """
    for iso2, entry in (cfg.get("countries") or {}).items():
        pats = entry.get("patterns", [])
        if _match_country_against_patterns(z_raw, pats) or _match_country_against_patterns(cleaned, pats):
            return iso2, entry.get("style"), True
    return None, None, False

# ---------- public ----------
def normalize_zip(country: str | None, zip_raw: str | None) -> ZipResult:
    """
    Универсальная нормализация ZIP.
    Выход ВСЕГДА: слитный A-Z0-9 без пробелов/дефисов (zip_norm).
    Валидность и country_inferred — по маскам; страну не меняем.
    """
    z_raw = (zip_raw or "").strip()
    if not z_raw:
        return ZipResult(zip_norm="", valid=False, country_inferred=None, style=None)

    cfg = _load_zip_cfg()
    cleaned = _clean_zip(z_raw)  # <-- это и будет zip_norm

    # Если страна известна — проверяем только её маски
    if country:
        entry = (cfg.get("countries") or {}).get((country or "").upper())
        if entry:
            pats = entry.get("patterns", [])
            valid = _match_country_against_patterns(z_raw, pats) or _match_country_against_patterns(cleaned, pats)
            return ZipResult(zip_norm=cleaned, valid=bool(valid), country_inferred=None, style=entry.get("style"))
        # страна известна, но профиля нет — просто вернуть слитный zip
        return ZipResult(zip_norm=cleaned, valid=False, country_inferred=None, style=None)

    # Страна неизвестна — пробуем угадать
    iso2, style, matched = _match_country(z_raw, cleaned, cfg)
    if matched:
        return ZipResult(zip_norm=cleaned, valid=True, country_inferred=iso2, style=style)

    # Ничего не подошло — мягкая нормализация без валидности
    return ZipResult(zip_norm=cleaned, valid=False, country_inferred=None, style=None)
