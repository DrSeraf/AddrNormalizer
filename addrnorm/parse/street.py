from __future__ import annotations
import re
from typing import Optional
from ..rules.registry import get_street_abbr

_WS = re.compile(r"\s+")
_EDGES_RE = re.compile(r"""^[\s"'“”„‚`«»\(\)\[\]\{\}.,;|/\\-]+|[\s"'“”„‚`«»\(\)\[\]\{\}.,;|/\\-]+$""")
APT_PAT = re.compile(
    r"\b("
    r"apt|apto|apartment|unit|suite|ste|room|rm|office|ofc|of\.?|"
    r"кв|кв\.?|квартира|офис|оф\.?|подъезд|под\.?|комн\.?|комната|пом\.?|помещение"
    r")\b.*$",
    flags=re.IGNORECASE,
)
NO_PAT = re.compile(r"\b(?:№|Nº|No\.?|N°)\s*(?=\d)", flags=re.IGNORECASE)

def _collapse_ws(s: str) -> str:
    return _WS.sub(" ", s).strip()

def _smart_title_word(w: str) -> str:
    if not w:
        return w
    if any(ch.isdigit() for ch in w):
        return w
    if len(w) <= 3 and w.isupper():
        return w
    return w[:1].upper() + w[1:].lower()

def _smart_title(s: str) -> str:
    tokens = []
    for tok in s.split(" "):
        subs = tok.split("-")
        subs = [_smart_title_word(x) for x in subs]
        tokens.append("-".join(subs))
    return " ".join(tokens)

def _script_of(s: str) -> str:
    for ch in s:
        if "\u0400" <= ch <= "\u04FF":
            return "cyrillic"
    return "latin"

def _build_alias_index() -> dict[str, dict[str, str]]:
    data = get_street_abbr() or {}
    idx: dict[str, dict[str, str]] = {"latin": {}, "cyrillic": {}}
    for group in ("latin", "cyrillic"):
        g = data.get(group) or {}
        for canon, aliases in g.items():
            canon_norm = str(canon).strip()
            for a in (aliases or []):
                k = str(a).strip().lower().replace(".", "")
                if not k:
                    continue
                idx[group][k] = canon_norm
    return idx

_ABBR_IDX = _build_alias_index()

def _normalize_abbr_tokens(s: str) -> str:
    if not _ABBR_IDX["latin"] and not _ABBR_IDX["cyrillic"]:
        return s
    group = _script_of(s)
    idx = _ABBR_IDX.get(group, {})
    if not idx:
        idx = {**_ABBR_IDX.get("latin", {}), **_ABBR_IDX.get("cyrillic", {})}

    out_words = []
    for w in s.split(" "):
        base = w.strip().strip(".")
        key = base.lower().replace(".", "")
        repl = idx.get(key)
        out_words.append(repl if repl else w)
    return " ".join(out_words)

def normalize_street(street_raw: Optional[str]) -> str:
    s = (street_raw or "")
    s = _collapse_ws(_EDGES_RE.sub("", s))
    if not s:
        return ""

    s = APT_PAT.sub("", s).strip(",; ")
    s = NO_PAT.sub("", s)
    s = _normalize_abbr_tokens(s)
    s = _collapse_ws(_EDGES_RE.sub("", s))
    s = _smart_title(s)

    # ---- финальная валидация ----
    # 1) если остались только цифры/знаки — очищаем
    only_digits = all(not ch.isalpha() for ch in s)
    if only_digits:
        return ""

    # 2) если букв меньше 4 — очищаем
    letters_count = sum(1 for ch in s if ch.isalpha())
    if letters_count < 4:
        return ""

    return s
