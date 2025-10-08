import streamlit as st
import pandas as pd
from io import StringIO

def upload_csv():
    f = st.file_uploader("Загрузите CSV", type=["csv"])
    if not f:
        return None
    content = f.getvalue().decode("utf-8", errors="replace")
    df = pd.read_csv(StringIO(content), dtype="string", keep_default_na=False, na_values=[])
    st.caption(f"Строк: {len(df)}, Колонок: {len(df.columns)}")
    # ↓ раскрыт сразу
    with st.expander("Первые строки", expanded=True):
        st.dataframe(df.head(20))
    return df
