from __future__ import annotations
import os, yaml
from typing import Optional, Dict, Any

_PROFILE_CACHE: Dict[str, Any] | None = None
_PROFILE_PATH: Optional[str] = None

ENV_VAR = "ADDRNORM_GEO_PROFILE"
FILENAME = "geo_profile.yaml"

def _is_file(path: Optional[str]) -> bool:
    return bool(path) and os.path.isfile(path)

def _try(path: str) -> Optional[str]:
    return path if _is_file(path) else None

def _candidates() -> list[str]:
    cand: list[str] = []
    # 1) Явный путь из окружения
    envp = os.getenv(ENV_VAR)
    if envp:
        cand.append(envp)

    # 2) Текущая рабочая директория
    cand.append(os.path.join(os.getcwd(), "configs", FILENAME))

    # 3) Подъём от расположения этого файла (__file__)
    here = os.path.abspath(os.path.dirname(__file__))  # .../addrnorm/rules
    root = here
    for _ in range(6):
        cand.append(os.path.join(root, "configs", FILENAME))
        root = os.path.abspath(os.path.join(root, ".."))

    # 4) Подъём от CWD
    cwd_root = os.getcwd()
    r = cwd_root
    for _ in range(6):
        cand.append(os.path.join(r, "configs", FILENAME))
        r = os.path.abspath(os.path.join(r, ".."))

    # Уникализируем, сохраняя порядок
    seen = set()
    uniq = []
    for p in cand:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq

def _find_profile_path() -> Optional[str]:
    for p in _candidates():
        if _is_file(p):
            return p
    return None

def _safe_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        obj = yaml.safe_load(f)
    return obj if isinstance(obj, dict) else {}

def _load_profile() -> dict:
    global _PROFILE_CACHE, _PROFILE_PATH
    if _PROFILE_CACHE is not None:
        return _PROFILE_CACHE

    _PROFILE_PATH = _find_profile_path()
    if not _PROFILE_PATH:
        _PROFILE_CACHE = {}
        return _PROFILE_CACHE

    try:
        _PROFILE_CACHE = _safe_yaml(_PROFILE_PATH)
    except Exception:
        _PROFILE_CACHE = {}
    return _PROFILE_CACHE

# ---- public helpers for UI ----
def get_profile_path() -> Optional[str]:
    """Вернёт фактический путь к geo_profile.yaml, если найден; иначе None."""
    if _PROFILE_PATH is None:
        _load_profile()
    return _PROFILE_PATH

def profile_loaded() -> bool:
    """True если профиль успешно найден и распарсен (dict не пустой)."""
    prof = _load_profile()
    return bool(prof)

# ---- getters ----
def get_country_index() -> dict[str, str]:
    prof = _load_profile()
    idx = ((prof.get("countries") or {}).get("index") or {})
    out: dict[str, str] = {}
    if isinstance(idx, dict):
        for k, v in idx.items():
            ks = str(k).strip().upper()
            vs = "" if v is None else str(v).strip()
            if ks and vs:
                out[ks] = vs
    return out

def get_country_aliases() -> dict[str, str]:
    prof = _load_profile()
    als = ((prof.get("countries") or {}).get("aliases") or {})
    out: dict[str, str] = {}
    if isinstance(als, dict):
        for k, v in als.items():
            ks = str(k).strip().lower()
            vs = "" if v is None else str(v).strip()
            if ks and vs:
                out[ks] = vs
    return out

def get_zip_patterns() -> dict[str, dict]:
    prof = _load_profile()
    zp = prof.get("zip_patterns") or {}
    out: dict[str, dict] = {}
    if isinstance(zp, dict):
        for iso2, entry in zp.items():
            if not isinstance(entry, dict):
                continue
            iso = str(iso2).strip().upper()
            patterns = entry.get("patterns") or []
            style = entry.get("style")
            out[iso] = {"patterns": list(patterns), "style": style}
    return out

def get_region_aliases(country_iso2: str | None) -> dict[str, str]:
    if not country_iso2:
        return {}
    prof = _load_profile()
    regs = prof.get("regions") or {}
    out: dict[str, str] = {}
    if isinstance(regs, dict):
        reg = regs.get(str(country_iso2).strip().upper()) or {}
        aliases = reg.get("aliases") or {}
        if isinstance(aliases, dict):
            for k, v in aliases.items():
                ks = str(k).strip().lower()
                ks = "".join(ch for ch in ks if ch.isalnum())  # убираем пробелы/точки/дефисы/_
                vs = "" if v is None else str(v).strip()
                if ks and vs:
                    out[ks] = vs
    return out

def get_street_abbr() -> dict[str, dict[str, list[str]]]:
    """
    Возвращает {"latin": {canon: [aliases...]}, "cyrillic": {...}} из configs/street_abbr/default.yaml.
    Если файл не найден/пуст — вернёт {}.
    """
    # пробуем найти рядом с профилем geo (ищем в той же корневой папке configs)
    base_dir = None
    p = get_profile_path()
    if p:
        base_dir = os.path.dirname(os.path.dirname(p))  # .../configs
    else:
        # fallback: от текущего рабочего каталога
        base_dir = os.path.join(os.getcwd(), "configs")

    path = os.path.join(base_dir, "street_abbr", "default.yaml")
    if not os.path.isfile(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        obj = yaml.safe_load(f)
    return obj if isinstance(obj, dict) else {}