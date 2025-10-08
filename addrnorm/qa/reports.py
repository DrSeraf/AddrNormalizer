from __future__ import annotations
import os, math, time
import pandas as pd

# keys -> красивое название
TITLE = {
    "changed": "ИЗМЕНЕНО",
    "cleared": "ОЧИЩЕНО",
}

def _iter_examples(before: pd.Series, after: pd.Series, colname: str):
    # генерирует (категория, строка)
    for i in range(len(before)):
        b = str(before.iloc[i]) if pd.notna(before.iloc[i]) else ""
        a = str(after.iloc[i]) if pd.notna(after.iloc[i]) else ""
        if b == a:
            continue
        if b and not a:
            yield ("cleared", f"[{colname}] строка {i+1}: \"{b}\" → \"\" (cleared)")
        else:
            yield ("changed", f"[{colname}] строка {i+1}: \"{b}\" → \"{a}\"")

def build_examples(changes: dict[str, tuple[pd.Series, pd.Series]], total: int = 20) -> list[str]:
    buckets = {"changed": [], "cleared": []}
    # Собираем сырые примеры по всем колонкам
    for col, (before, after) in changes.items():
        for cat, line in _iter_examples(before, after, col):
            buckets[cat].append(line)

    # Равномерная выборка по категориям
    kinds = [k for k in ["changed","cleared"] if buckets[k]]
    if not kinds:
        return ["Нет изменений для показа."]
    per = max(1, total // len(kinds))
    out = []
    for k in kinds:
        out.append(f"===== {TITLE[k]} =====")
        out.extend(buckets[k][:per])
    # Если осталось место — добираем из любых категорий
    remain = total - sum(per for _ in kinds)
    if remain > 0:
        pool = []
        for k in kinds:
            pool.extend(buckets[k][per:])
        out.extend(pool[:remain])
    return out

def save_examples_txt(lines: list[str], logs_dir: str = "logs") -> str:
    os.makedirs(logs_dir, exist_ok=True)
    path = os.path.join(logs_dir, f"examples_{int(time.time())}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
