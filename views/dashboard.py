import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from utils.data_loader import load_properties, load_infrastructure
from utils.logger import setup_logger
from components.map_utils import create_mini_map
from utils.preprocess_data import preprocess_data

import numpy as np

logger = setup_logger(__name__)

def show_dashboard():
    """Рендер главной страницы с реальными данными"""
    st.title("📊 Аналитическая система недвижимости")
    st.markdown("---")
    
    try:
        # Загрузка данных
        properties = load_properties()
        infrastructure = load_infrastructure()
        
        # Предобработка данных
        properties = preprocess_data(properties)
        
        # Блок быстрого поиска
        render_search_block(properties)
        
        # Информационные карточки
        render_info_cards(properties)
        
        # Мини-карта
        render_mini_map(properties, infrastructure)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки dashboard: {e}")
        st.exception(e)
        st.error("Произошла ошибка при загрузке данных. Пожалуйста, попробуйте позже.")

def render_search_block(properties):
    """Блок быстрого поиска недвижимости"""
    with st.container():
        st.subheader("🔍 Быстрый поиск недвижимости")
        
        col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
        
        with col1:
            # Автодополнение адресов из реальных данных
            unique_addresses = properties['address'].unique().tolist()
            address = st.selectbox(
                "Адрес или район", 
                options=[""] + unique_addresses,
                index=0,
                key="search_address"
            )
        
        with col2:
            property_types = ["Все"] + properties['type'].unique().tolist()
            property_type = st.selectbox(
                "Тип жилья", 
                options=property_types,
                index=0,
                key="search_type"
            )
        
        with col3:
            room_options = ["Все"] + sorted(properties['num_rooms'].unique().tolist())
            rooms = st.selectbox(
                "Комнат", 
                options=room_options,
                index=0,
                key="search_rooms"
            )
        
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Найти", type="primary", key="search_btn"):
                # Сохраняем параметры поиска
                st.session_state.search_params = {
                    'address': address,
                    'type': property_type,
                    'rooms': rooms
                }
                # Переходим на страницу карты
                st.session_state.page = "map"
                st.rerun()
    
    st.markdown("---")

def render_info_cards(properties):
    """Информационные карточки с аналитикой"""
    st.subheader("📈 Ключевые показатели")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Карточка средней цены
        avg_price = properties['price_per_m2'].mean()
        
        # Расчет изменения цены за последний месяц
        if 'date' in properties.columns:
            last_month = datetime.now() - timedelta(days=30)
            monthly_data = properties[properties['date'] >= last_month]
            if len(monthly_data) > 0:
                current_avg = monthly_data['price_per_m2'].mean()
                prev_avg = properties[properties['date'] < last_month]['price_per_m2'].mean()
                price_change = ((current_avg - prev_avg) / prev_avg) * 100
                delta_text = f"{price_change:.1f}% за месяц"
            else:
                delta_text = "Нет данных"
        else:
            delta_text = "Нет данных"
        
        st.metric(
            label="Средняя цена по городу", 
            value=f"{avg_price:,.0f} руб./м²", 
            delta=delta_text
        )
        
        # График изменения цен
        if 'date' in properties.columns:
            price_trend = properties.resample('ME', on='date')['price_per_m2'].mean().reset_index()
            fig = px.line(
                price_trend, 
                x='date', 
                y='price_per_m2',
                title='Динамика цен за м²',
                labels={'date': 'Дата', 'price_per_m2': 'Цена за м²'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Данные о динамике цен недоступны")
    
    with col2:
        # Популярные районы (топ-5 по количеству объявлений)
        st.subheader("🏙️ Популярные районы")
        
        # Извлекаем район из адреса (пример: "ул. Ленина, д.10" -> "Ленина")
        properties['district'] = properties['address'].str.extract(r'ул\. (\w+)')[0]
        district_stats = properties['district'].value_counts().nlargest(5)
        
        for district, count in district_stats.items():
            percentage = (count / len(properties)) * 100
            st.progress(
                percentage / 100, 
                text=f"{district}: {percentage:.1f}% объявлений"
            )
    
    with col3:
        # Новости рынка (можно подключить API или базу данных)
        st.subheader("📰 Последние новости")
        
        news = get_market_news()  # Функция для получения новостей
        
        for item in news:
            with st.expander(f"{item['date']}: {item['title']}"):
                st.write(item['content'])
                if st.button("Подробнее →", key=f"news_{item['id']}"):
                    st.session_state.news_detail = item
                    # Здесь можно добавить переход на детальную страницу
    
    st.markdown("---")

def get_market_news():
    """Получение новостей рынка (заглушка)"""
    # В реальном приложении можно подключить API или базу данных
    return [
        {
            'id': 1,
            'date': '15.06.2023',
            'title': 'Ипотечные ставки снижены',
            'content': 'ЦБ РФ снизил ключевую ставку, что привело к снижению ипотечных ставок...'
        },
        {
            'id': 2,
            'date': '10.06.2023',
            'title': 'Новые ЖК в вашем городе',
            'content': 'Завершено строительство трех новых жилых комплексов...'
        }
    ]

def render_mini_map(properties, infrastructure):
    """Мини-карта с тепловым отображением цен"""
    st.subheader("🗺️ Тепловая карта цен")
    
    # Создаем мини-карту
    st.pydeck_chart(create_mini_map(properties, infrastructure))
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Перейти к полной карте", key="go_to_map", use_container_width=True):
            st.session_state.page = "map"
            st.rerun()
    
    st.markdown("---")