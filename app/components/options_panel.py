import streamlit as st

def render_options():
    st.sidebar.header("Параметры")

    output_mode = st.sidebar.radio(
        "Режим вывода",
        options=["addr-only", "extended"],
        index=0,
        help="addr-only: все исходные колонки + country_norm + addr_norm. extended: нормализованные поля."
    )

    # libpostal
    use_libpostal = st.sidebar.checkbox(
        "Post-process через libpostal REST",
        value=False,
        help="После базовой очистки прогонять адрес через libpostal REST (медленнее)."
    )
    libpostal_url = st.sidebar.text_input(
        "Libpostal REST URL",
        value="http://localhost:8080",
        help="Базовый URL контейнера libpostal-rest (например, http://localhost:8080)."
    )

    return {
        "output_mode": output_mode,
        "use_libpostal": use_libpostal,
        "libpostal_url": libpostal_url,
    }
