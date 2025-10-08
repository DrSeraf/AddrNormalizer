from __future__ import annotations
import os, time
import pandas as pd
from typing import Tuple, List

ORDER = ["street", "locality", "district", "region", "country", "zip"]
MAX_VALUE_LEN = 200  # обрезаем каждое значение в логе до 200 символов

def _trim(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\r", " ").replace("\n", " ")  # без переносов
    if len(s) <= MAX_VALUE_LEN:
        return s
    return s[:MAX_VALUE_LEN] + "…"

def _iter_changes(before: pd.Series, after: pd.Series, colname: str) -> List[str]:
    out: List[str] = []
    n = len(before)
    for i in range(n):
        b_raw = "" if pd.isna(before.iloc[i]) else str(before.iloc[i])
        a_raw = "" if pd.isna(after.iloc[i])  else str(after.iloc[i])
        if b_raw == a_raw:
            continue
        b = _trim(b_raw)
        a = _trim(a_raw)
        if b and not a:
            out.append(f"[{colname}] строка {i+1}: \"{b}\" → \"\" (cleared)")
        else:
            out.append(f"[{colname}] строка {i+1}: \"{b}\" → \"{a}\"")
    return out

def _even_sample(items: List[str], limit: int) -> List[str]:
    """Равномерная выборка по массиву без numpy; защищена от дублей."""
    if limit is None or limit <= 0 or len(items) <= limit:
        return items
    if len(items) == 0:
        return items
    if limit == 1:
        return [items[0]]
    step = (len(items) - 1) / (limit - 1)
    idxs = [round(i * step) for i in range(limit)]
    seen = set()
    result = []
    for i in idxs:
        if i not in seen:
            seen.add(i)
            result.append(items[i])
    j = 0
    while len(result) < limit and j < len(items):
        if j not in seen:
            result.append(items[j])
        j += 1
    return result

def build_columnwise_report(changes: dict[str, Tuple[pd.Series, pd.Series]], per_col_limit: int = 20) -> list[str]:
    """
    Длинный список секций по колонкам в порядке ORDER.
    В каждой секции: ≤ per_col_limit равномерно распределённых примеров.
    Если нет изменений — строка 'нет изменений.'.
    """
    lines: list[str] = []
    for col in ORDER:
        lines.append(f"========== {col} ==========")
        if col not in changes:
            lines.append("нет изменений.")
            continue
        before, after = changes[col]
        diffs = _iter_changes(before, after, col)
        if not diffs:
            lines.append("нет изменений.")
            continue
        lines.extend(_even_sample(diffs, per_col_limit))
    return lines

def save_examples_txt(lines: list[str], logs_dir: str = "logs") -> str:
    os.makedirs(logs_dir, exist_ok=True)
    path = os.path.join(logs_dir, f"examples_{int(time.time())}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
