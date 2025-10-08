# reader.py
import pandas as pd

DEFAULT_COLS = ["address","zip","country","region","district","locality","street"]

def read_csv_any(path: str, dtype="string") -> pd.DataFrame:
    return pd.read_csv(path, dtype=dtype, keep_default_na=False, na_values=[])

def safe_get(df, col):
    return df[col] if col in df.columns else pd.Series([""]*len(df), dtype="string")
