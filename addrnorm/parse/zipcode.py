from __future__ import annotations
import re, os, yaml
from dataclasses import dataclass

_ZIP_CFG_CACHE: dict | None = None

@dataclass
class ZipResult:
    zip_norm: str
    valid: bool
    country_inferred: str | None
    style: str | None

def _load_zip_cfg() -> dict:
    global _ZIP_CFG_CACHE
    if _ZIP_CFG_CACHE is not None:
        return _ZIP_CFG_CACHE
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs", "zip_patterns.yaml")
    if not os.path.exists(cfg_path):
        # дефолтный минимум, если yaml не найден
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
_ALNUM_RE = re.compile(r"[A-Za-z0-9]+")

def _clean_zip(s: str) -> str:
    if not s:
        return ""
    s = str(s).strip()
    # Оставляем только буквы/цифры и одинарные пробелы/дефисы по месту форматирования — форматы ниже их вернут
    return "".join(_ALNUM_RE.findall(s)).upper()

def _fmt_by_style(style: str, raw: str) -> str:
    # style → каноническое форматирование (raw — уже очищен, только A-Z0-9)
    if style == "US":
        if len(raw) == 5:  return raw
        if len(raw) == 9:  return f"{raw[:5]}-{raw[5:]}"
    elif style == "CA":
        # A1A 1A1
        if len(raw) == 6:
            return f"{raw[:3]} {raw[3:]}"
    elif style == "GB":
        # Упрощённо: пробел перед последними 3 символами
        if len(raw) >= 5:
            return f"{raw[:-3]} {raw[-3:]}"
    elif style == "NL":
        # 1234 AB
        if len(raw) == 6:
            return f"{raw[:4]} {raw[4:]}"
    elif style == "PL":
        # 12-345
        if len(raw) == 5:
            return f"{raw[:2]}-{raw[2:]}"
    elif style == "PT":
        # 1234-567 (7 цифр)
        if len(raw) == 7:
            return f"{raw[:4]}-{raw[4:]}"
    elif style == "BR":
        # 12345-678 (8 цифр)
        if len(raw) == 8:
            return f"{raw[:5]}-{raw[5:]}"
    elif style == "JP":
        # 123-4567
        if len(raw) == 7:
            return f"{raw[:3]}-{raw[3:]}"
    elif style == "IE":
        # A65 F4E2 (7 алф-цифр)
        if len(raw) == 7:
            return f"{raw[:3]} {raw[3:]}"
    elif style == "N4":
        if len(raw) == 4: return raw
    elif style == "N5":
        if len(raw) == 5: return raw
    elif style == "N6":
        if len(raw) == 6: return raw
    # по умолчанию — вернуть как есть
    return raw

def _match_country(raw: str, cfg: dict) -> tuple[str|None, str|None]:
    """Возвращает (ISO2, style) первой страны, чьи паттерны совпали."""
    countries = (cfg.get("countries") or {})
    for iso2, entry in countries.items():
        pats = entry.get("patterns", [])
        for p in pats:
            if re.match(p, raw, flags=re.IGNORECASE):
                return iso2, entry.get("style")
    return None, None

# ---------- public ----------
def normalize_zip(country: str | None, zip_raw: str | None) -> ZipResult:
    """Универсальная нормализация ZIP. Не меняет страну; при None пытается угадать country_inferred."""
    z = (zip_raw or "").strip()
    if not z:
        return ZipResult(zip_norm="", valid=False, country_inferred=None, style=None)

    cfg = _load_zip_cfg()
    # 1) очищаем до A-Z0-9
    cleaned = _clean_zip(z)

    # 2) если страна известна — проверяем только её маски
    if country:
        entry = (cfg.get("countries") or {}).get((country or "").upper())
        if entry:
            # сначала проверим паттерны по сырому вводу (допуская пробел/дефис как в yaml)
            for p in entry.get("patterns", []):
                if re.match(p, z.strip(), flags=re.IGNORECASE):
                    # форматируем
                    return ZipResult(_fmt_by_style(entry.get("style",""), cleaned), True, None, entry.get("style"))
            # иначе — проверим по очищенному
            for p in entry.get("patterns", []):
                if re.match(p, cleaned, flags=re.IGNORECASE):
                    return ZipResult(_fmt_by_style(entry.get("style",""), cleaned), True, None, entry.get("style"))
        # страна известна, но паттерны не совпали — вернём просто очищенный
        return ZipResult(cleaned, False, None, None)

    # 3) страна неизвестна — попробуем по всем маскам (сначала по сырому, затем по cleaned)
    iso2, style = _match_country(z.strip(), cfg)
    if iso2 and style:
        return ZipResult(_fmt_by_style(style, cleaned), True, iso2, style)
    iso2, style = _match_country(cleaned, cfg)
    if iso2 and style:
        return ZipResult(_fmt_by_style(style, cleaned), True, iso2, style)

    # 4) ничего не подошло — «мягкая» нормализация
    return ZipResult(cleaned, False, None, None)
