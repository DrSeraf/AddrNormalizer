from __future__ import annotations
import os, yaml

_PROFILE_CACHE: dict | None = None

def _project_root_from_here() -> str:
    # .../addrnorm/rules/registry.py -> подняться на 3 уровня до корня проекта
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def _profile_path() -> str:
    return os.path.join(_project_root_from_here(), "configs", "geo_profile.yaml")

def _load_profile() -> dict:
    global _PROFILE_CACHE
    if _PROFILE_CACHE is not None:
        return _PROFILE_CACHE
    path = _profile_path()
    data: dict = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            obj = yaml.safe_load(f)
            data = obj if isinstance(obj, dict) else {}
    else:
        # на всякий случай — попробуем legacy-путь (если кто-то положил внутрь пакета)
        legacy = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "geo_profile.yaml")
        if os.path.exists(legacy):
            with open(legacy, "r", encoding="utf-8") as f:
                obj = yaml.safe_load(f)
                data = obj if isinstance(obj, dict) else {}
    _PROFILE_CACHE = data
    return _PROFILE_CACHE

# ----- countries -----
def get_country_index() -> dict[str, str]:
    prof = _load_profile()
    idx = ((prof.get("countries") or {}).get("index") or {})
    out: dict[str, str] = {}
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
    for k, v in als.items():
        ks = str(k).strip().lower()
        vs = "" if v is None else str(v).strip()
        if ks and vs:
            out[ks] = vs
    return out

# ----- ZIP patterns -----
def get_zip_patterns() -> dict[str, dict]:
    prof = _load_profile()
    zp = prof.get("zip_patterns") or {}
    out: dict[str, dict] = {}
    for iso2, entry in zp.items():
        iso = str(iso2).strip().upper()
        if not iso or not isinstance(entry, dict):
            continue
        patterns = entry.get("patterns") or []
        style = entry.get("style")
        out[iso] = {"patterns": list(patterns), "style": style}
    return out

# ----- regions -----
def get_region_aliases(country_iso2: str | None) -> dict[str, str]:
    if not country_iso2:
        return {}
    prof = _load_profile()
    iso = str(country_iso2).strip().upper()
    reg = ((prof.get("regions") or {}).get(iso) or {})
    aliases = reg.get("aliases") or {}
    out: dict[str, str] = {}
    for k, v in aliases.items():
        ks = str(k).strip().lower()
        # удаляем пробелы/точки/дефисы/подчёркивания
        ks = "".join(ch for ch in ks if ch.isalnum())
        vs = "" if v is None else str(v).strip()
        if ks and vs:
            out[ks] = vs
    return out
