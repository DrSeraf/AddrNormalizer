from __future__ import annotations
import re
from typing import Optional

# ---------- базовые утилиты ----------
def _collapse_ws(s: str) -> str:
    s = re.sub(r"\s+", " ", s, flags=re.UNICODE)
    return s.strip(" \t\n\r,;|/")

_EDGES_RE = re.compile(r"""^[\s"'“”„‚`«»\(\)\[\]\{\}]+|[\s"'“”„‚`«»\(\)\[\]\{\}]+$""")

_PREFIXES = [
    r"city of", r"municipality of", r"town of", r"village of",
    r"ciudad de", r"cidade de", r"ville de", r"gemeente", r"stad",
    r"г\.?", r"город", r"пос[. ]?", r"пгт", r"рп", r"с[.\s]?|село|деревня|дер[.]?",
    r"кп", r"аул", r"кишлак",
]
_PREFIXES_RE = re.compile(rf"^({'|'.join(_PREFIXES)})\s+", flags=re.IGNORECASE)

_PARENS_NOISE_RE = re.compile(
    r"\((?:[^)]*район[^)]*|[^)]*округ[^)]*|[^)]*municipality[^)]*|[^)]*county[^)]*|[^)]*district[^)]*)\)",
    re.IGNORECASE,
)

_GARBAGE = {"", "n/a", "na", "null", "none", "-", "unknown", "неизвестно"}

def _smart_title(s: str) -> str:
    parts = []
    for token in s.split(" "):
        subparts = []
        for sub in token.split("-"):
            if not sub:
                subparts.append(sub)
                continue
            if any(ch.isdigit() for ch in sub):
                subparts.append(sub)
            else:
                subparts.append(sub[:1].upper() + sub[1:].lower())
        parts.append("-".join(subparts))
    return " ".join(parts)

def _first_meaningful_segment(s: str) -> str:
    seg = re.split(r"[,/|]", s, maxsplit=1)[0].strip()
    return seg or s

# ---------- корректная проверка "похоже на ZIP" ----------
_ZIPLIKE_PATTERNS = [
    re.compile(r"^\d{3,8}$"),                     # просто цифры (многие страны)
    re.compile(r"^\d{5}-\d{4}$"),                 # US ZIP+4
    re.compile(r"^\d{5}-\d{3}$"),                 # BR
    re.compile(r"^\d{3}-\d{4}$"),                 # JP
    re.compile(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$"),  # CA
    re.compile(r"^\d{4}\s?[A-Za-z]{2}$"),         # NL
    re.compile(r"^\d{2}-\d{3}$"),                 # PL
    re.compile(r"^\d{4}-\d{3}$"),                 # PT
    re.compile(r"^[A-Za-z]\d{2}\s?[A-Za-z\d]{4}$"),      # IE
]

def _looks_like_zip(s: str) -> bool:
    for pat in _ZIPLIKE_PATTERNS:
        if pat.match(s):
            return True
    return False

# ---------- публичная функция ----------
def normalize_locality(locality_raw: Optional[str], country_iso2: Optional[str] = None, country_name: Optional[str] = None) -> str:
    """
    Базовая нормализация названия населённого пункта (язык-агностично).
    Шаги:
      1) trim + collapse spaces
      2) снять внешние кавычки/скобки, вырезать «админ.» скобки внутри
      3) срезать типовые префиксы (г., city of, …)
      4) взять первую осмысленную часть до запятой/слеша
      5) привести регистр (Title-Case с поддержкой дефисов)
      6) отсеять мусор и только РЕАЛЬНО zip-подобные значения
    """
    s = (locality_raw or "")
    s = _collapse_ws(s)
    if not s:
        return ""

    s = _EDGES_RE.sub("", s)
    s = _collapse_ws(_PARENS_NOISE_RE.sub("", s))
    s = _PREFIXES_RE.sub("", s)
    s = _first_meaningful_segment(s)
    s = _collapse_ws(_EDGES_RE.sub("", s))

    if not s or s.lower() in _GARBAGE:
        return ""

    # отбрасываем явные ZIP-подобные значения (цифровые форматы и самые частые шаблоны)
    if _looks_like_zip(s):
        return ""

    # нормализуем регистр
    s = _smart_title(s)
    return s
