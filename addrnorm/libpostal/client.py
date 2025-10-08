from __future__ import annotations
import json
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple, Optional

class LibPostalError(Exception):
    pass

class LibPostalClient:
    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 5.0, retries: int = 1):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = max(0, retries)

    def _get(self, path: str, q: Dict[str, str]) -> Tuple[int, str]:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(q)}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            code = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
            return code, body

    def parse(self, text: str) -> List[Dict[str, str]]:
        """
        Ожидаемый ответ libpostal-rest: [{"label":"road","value":"main"}, ...]
        Встречается и форма: {"components":[...]} — поддерживаем обе.
        """
        if not text:
            return []
        last_err: Optional[Exception] = None
        for _ in range(self.retries + 1):
            try:
                code, body = self._get("/parse", {"text": text})
                if code != 200:
                    raise LibPostalError(f"HTTP {code}: {body[:200]}")
                data = json.loads(body)
                if isinstance(data, dict) and isinstance(data.get("components"), list):
                    return list(data["components"])
                if isinstance(data, list):
                    return [x for x in data if isinstance(x, dict) and "label" in x and "value" in x]
                return []
            except Exception as e:
                last_err = e
        raise LibPostalError(str(last_err) if last_err else "unknown error")
