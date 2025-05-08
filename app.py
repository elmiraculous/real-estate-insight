import streamlit as st
from views.dashboard import show_dashboard
from views.map_view import show_map_page
from views.analytics import show_analytics_page
from views.forecasting import show_forecasting_page
from views.account import show_account_page
from utils.check_auth import check_auth
from utils.logger import setup_logger
import logging
from config import APP_CONFIG

# Настройка логгера
logger = setup_logger(__name__)

def main():
    # Инициализация состояния сессии
    init_session_state()
    
    # Настройка страницы
    st.set_page_config(
        page_title="Real Estate Analytics",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={}
    )
    
    # Проверка аутентификации
    if not check_auth():
        st.warning("Пожалуйста, войдите в систему")
        return
    
    # Отображение навигационного меню
    render_sidebar()
    
    # Отображение текущей страницы
    render_current_page()
    
    # Отладка состояния сессии (можно закомментировать)
    # if APP_CONFIG.get('debug', False):
    #     st.sidebar.markdown("---")
    #     st.sidebar.subheader("Отладка")
    #     st.sidebar.write(st.session_state)

def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    if 'search_query' not in st.session_state:
        st.session_state.search_query = None
    
    if 'user' not in st.session_state:
        st.session_state.user = {
            'authenticated': True,  
            'username': 'demo_user',
            'role': 'analyst'
        }

def render_sidebar():
    """Отрисовка боковой панели навигации"""
    with st.sidebar:
        st.markdown("## Навигация")
        
        # Кнопки навигации
        nav_options = {
            'dashboard': {'icon': '🏠', 'label': 'Главная'},
            'map': {'icon': '🗺️', 'label': 'Карта'},
            'analytics': {'icon': '📊', 'label': 'Аналитика'},
            'forecasting': {'icon': '🔮', 'label': 'Прогнозы'},
            'account': {'icon': '👤', 'label': 'Мой кабинет'}
        }
        
        for page, config in nav_options.items():
            if st.button(f"{config['icon']} {config['label']}", key=f"nav_{page}"):
                st.session_state.page = page
                st.rerun()
        
        st.markdown("---")
        
        # Кнопка входа/регистрации
        if st.session_state.user['authenticated']:
            st.markdown(f"Вы вошли как **{st.session_state.user['username']}**")
            if st.button("🚪 Выйти", key="logout_btn"):
                st.session_state.user['authenticated'] = False
                st.rerun()
        else:
            if st.button("🔑 Войти / Зарегистрироваться", key="login_btn"):
                st.session_state.show_login = True
                st.rerun()

def render_current_page():
    """Отрисовка текущей страницы на основе состояния сессии"""
    try:
        if st.session_state.page == 'dashboard':
            show_dashboard()
        elif st.session_state.page == 'map':
            show_map_page()
        elif st.session_state.page == 'analytics':
            show_analytics_page()
        elif st.session_state.page == 'forecasting':
            show_forecasting_page()
        elif st.session_state.page == 'account':
            show_account_page()
        else:
            st.warning("Страница не найдена")
            st.session_state.page = 'dashboard'
            st.rerun()
            
    except Exception as e:
        logger.error(f"Ошибка отрисовки страницы: {e}")
        st.error("Произошла ошибка при загрузке страницы")
        if APP_CONFIG.get('debug', False):
            st.exception(e)

if __name__ == "__main__":
    main()