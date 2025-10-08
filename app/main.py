# --- make project root importable ---
import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ------------------------------------

import streamlit as st
import pandas as pd
from addrnorm.logging_cfg.setup import setup_logging
from addrnorm.io.writer import process_dataframe, write_csv
from app.components.options_panel import render_options
from app.components.file_uploader import upload_csv
from addrnorm.qa.reports import build_examples, save_examples_txt
import time

st.set_page_config(page_title="AddrNormalizer", layout="wide")

logger = setup_logging(logs_dir="logs", level="INFO")
st.title("AddrNormalizer — нормализация адресов (v0)")

opts = render_options()
df = upload_csv()

# Кнопка запуска
run = st.button("🚀 Запустить обработку", type="primary", disabled=df is None)

if run and df is not None:
    st.markdown("---")
    st.subheader("Обработка")
    with st.spinner("Нормализация..."):
        t0 = time.time()
        out, changes = process_dataframe(df, output_mode=opts["output_mode"])
        dt = time.time() - t0
        logger.info("Processed %s rows in %.2fs (mode=%s)", len(df), dt, opts["output_mode"])

    st.success(f"Готово: {len(out)} строк за {dt:.2f} сек")
    st.dataframe(out.head(20))

    # Сохранение результата
    os.makedirs("data/output", exist_ok=True)
    out_name = f"data/output/addrnorm_{int(time.time())}.csv"
    write_csv(out, out_name)

    # Формируем и показываем примеры изменений
    st.subheader("Логи примеров (20 шт.)")
    example_lines = build_examples(changes, total=20)
    example_txt_path = save_examples_txt(example_lines, logs_dir="logs")

    st.code("\n".join(example_lines), language="text")
    st.caption(f"Лог-файл (примеры): {example_txt_path}")
    st.caption(f"Полный лог: {logger.log_path}")

    # Кнопка скачивания результирующего CSV
    with open(out_name, "rb") as f:
        st.download_button("Скачать результат CSV", f, file_name=os.path.basename(out_name), mime="text/csv")
else:
    if df is None:
        st.info("Загрузите файл для старта.")
