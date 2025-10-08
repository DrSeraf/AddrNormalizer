import re
import unicodedata

SPACE_RE = re.compile(r"\s+", re.UNICODE)

def norm_text(s: str | None) -> str:
    if s is None: 
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u00A0", " ")  # nbsp -> space
    s = SPACE_RE.sub(" ", s).strip(" ,;")
    return s

def is_garbage(s: str) -> bool:
    if not s:
        return True
    bad = {"n/a","na","null","none","-","*","all states","?"}
    return s.lower().strip() in bad
