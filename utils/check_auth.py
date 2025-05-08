import streamlit as st

def check_auth():
    """Фиктивная проверка аутентификации для демо"""
    user = st.session_state.get("user", {})
    return user.get("authenticated", False)
