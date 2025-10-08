from __future__ import annotations
import os, time
import pandas as pd

ORDER = ["street", "locality", "district", "region", "country", "zip"]

def _iter_examples(before: pd.Series, after: pd.Series, colname: str):
    """Генерирует строки 'до → после' по колонке."""
    for i in range(len(before)):
        b = "" if pd.isna(before.iloc[i]) else str(before.iloc[i])
        a = "" if pd.isna(after.iloc[i])  else str(after.iloc[i])
        if b == a:
            continue
        if b and not a:
            yield f"[{colname}] строка {i+1}: \"{b}\" → \"\" (cleared)"
        else:
            yield f"[{colname}] строка {i+1}: \"{b}\" → \"{a}\""

def build_columnwise_report(changes: dict[str, tuple[pd.Series, pd.Series]], per_col_limit: int | None = None) -> list[str]:
    """
    Возвращает длинный список строк с секциями по колонкам в ORDER.
    Если колонки нет в changes — выводит секцию и 'нет изменений'.
    per_col_limit=None -> показывать все изменения колонки.
    """
    lines: list[str] = []
    for col in ORDER:
        lines.append(f"========== {col} ==========")
        if col not in changes:
            lines.append("нет изменений.")
            continue
        before, after = changes[col]
        bucket = list(_iter_examples(before, after, col))
        if not bucket:
            lines.append("нет изменений.")
            continue
        if per_col_limit is not None and per_col_limit > 0:
            bucket = bucket[:per_col_limit]
        lines.extend(bucket)
    return lines

def save_examples_txt(lines: list[str], logs_dir: str = "logs") -> str:
    os.makedirs(logs_dir, exist_ok=True)
    path = os.path.join(logs_dir, f"examples_{int(time.time())}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
