# --- make project root importable ---
import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ------------------------------------

import time
import streamlit as st

from addrnorm.logging_cfg.setup import setup_logging
from addrnorm.io.writer import process_dataframe, write_csv
from app.components.options_panel import render_options
from app.components.file_uploader import upload_csv
from addrnorm.qa.reports import build_columnwise_report, save_examples_txt

st.set_page_config(page_title="AddrNormalizer", layout="wide")

logger = setup_logging(logs_dir="logs", level="INFO")
st.title("AddrNormalizer — нормализация адресов")

# Параметры (режим addr-only | extended и т.д.)
opts = render_options()

# Загрузка CSV с автопревью (expander открыт в компоненте)
df = upload_csv()

# Кнопка запуска обработки
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

    # Сохранение результата и кнопка скачивания
    os.makedirs("data/output", exist_ok=True)
    out_path = f"data/output/addrnorm_{int(time.time())}.csv"
    write_csv(out, out_path)
    with open(out_path, "rb") as f:
        st.download_button("Скачать результат CSV", f, file_name=os.path.basename(out_path), mime="text/csv")

    # Помодульные логи изменений по колонкам (street → locality → district → region → country → zip)
    st.subheader("Логи изменений по колонкам")
    lines = build_columnwise_report(changes, per_col_limit=None)  # без лимита — покажем всё
    examples_path = save_examples_txt(lines, logs_dir="logs")

    st.code("\n".join(lines), language="text")
    st.caption(f"Лог-примеры: {examples_path}")
    st.caption(f"Полный лог: {logger.log_path}")

elif df is None:
    st.info("Загрузите файл для старта.")
