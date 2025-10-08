import streamlit as st

def render_options():
    st.sidebar.subheader("Параметры")
    output_mode = st.sidebar.radio(
        "Режим вывода",
        options=["addr-only","extended"],
        format_func=lambda x: "Только addr_norm" if x=="addr-only" else "Расширенный набор",
        index=0
    )
    profile = st.sidebar.selectbox("Профиль страны", options=["auto","US","RU","ES","DE"], index=0)
    libpostal = st.sidebar.toggle("libpostal post-process", value=False)
    return {"output_mode": output_mode, "profile": profile, "libpostal": libpostal}
