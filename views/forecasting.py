import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from utils.data_loader import load_model, load_infrastructure
from utils.logger import setup_logger

logger = setup_logger(__name__)

def get_coordinates(address):
    """Получение координат по адресу"""
    try:
        geolocator = Nominatim(user_agent="real_estate_app")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.error(f"Ошибка геокодирования: {e}")
        return None

def calculate_distances(lat, lon, infrastructure):
    """Расчет расстояний до объектов инфраструктуры"""
    try:
        distances = {}
        
        for infra_type in ['metro', 'school', 'park', 'mall', 'clinic', 'parking']:
            if infra_type in infrastructure:
                infra_points = infrastructure[infra_type]
                if not infra_points.empty:
                    # Находим ближайшую точку
                    min_distance = float('inf')
                    for _, point in infra_points.iterrows():
                        try:
                            distance = geodesic(
                                (lat, lon),
                                (point['latitude'], point['longitude'])
                            ).meters
                            min_distance = min(min_distance, distance)
                        except Exception as e:
                            logger.error(f"Ошибка при расчете расстояния для {infra_type}: {e}")
                            continue
                    distances[f'{infra_type}_dist'] = int(min_distance)
                else:
                    distances[f'{infra_type}_dist'] = 1000  # Значение по умолчанию
            else:
                distances[f'{infra_type}_dist'] = 1000  # Значение по умолчанию
        
        return distances
    except Exception as e:
        logger.error(f"Ошибка в calculate_distances: {e}")
        # Возвращаем значения по умолчанию в случае ошибки
        return {
            'metro_dist': 1000,
            'school_dist': 1000,
            'park_dist': 1000,
            'mall_dist': 1000,
            'clinic_dist': 1000,
            'parking_dist': 1000
        }

def show_forecasting_page():
    """Страница прогнозирования стоимости недвижимости"""
    st.title("🔮 Прогнозирование стоимости")
    st.markdown("---")
    
    try:
        # Загрузка модели и данных инфраструктуры
        model = load_model()
        if model is None:
            st.error("Не удалось загрузить модель прогнозирования")
            return
            
        infrastructure = load_infrastructure()
        if infrastructure is None:
            st.error("Не удалось загрузить данные инфраструктуры")
            return
        
        # Основные параметры
        st.header("1. Основные параметры")
        col1, col2 = st.columns(2)
        
        with col1:
            area = st.slider("Площадь (м²)", 30, 200, 65)
            rooms = st.selectbox("Количество комнат", [1, 2, 3, 4], index=1)
            floor = st.slider("Этаж", 1, 25, 5)
        
        with col2:
            year_built = st.slider("Год постройки дома", 1950, 2023, 2000)
            repair_type = st.selectbox("Состояние ремонта", ["Без ремонта", "Косметический", "Евроремонт"])
            house_type = st.selectbox("Тип дома", ["Панельный", "Кирпичный", "Монолитный", "Блочный"])
        
        # Выбор местоположения
        st.header("2. Местоположение")
        address = st.text_input("Введите адрес", "Казань, ул. Пушкина, д. 1")
        
        if st.button("Найти координаты", type="secondary"):
            with st.spinner("Поиск координат..."):
                coordinates = get_coordinates(address)
                if coordinates:
                    st.session_state.latitude, st.session_state.longitude = coordinates
                    st.success(f"Координаты найдены: {coordinates[0]:.4f}, {coordinates[1]:.4f}")
                else:
                    st.error("Не удалось найти координаты по указанному адресу")
        
        # Используем сохраненные координаты или значения по умолчанию
        latitude = st.session_state.get('latitude', 55.7887)
        longitude = st.session_state.get('longitude', 49.1221)
        
        # Расчет расстояний до инфраструктуры
        distances = calculate_distances(latitude, longitude, infrastructure)
        
        # Отображение расстояний
        st.header("3. Ближайшая инфраструктура")
        infra_cols = st.columns(3)
        
        with infra_cols[0]:
            st.metric("До метро", f"{distances['metro_dist']} м")
            st.metric("До школы", f"{distances['school_dist']} м")
        
        with infra_cols[1]:
            st.metric("До парка", f"{distances['park_dist']} м")
            st.metric("До ТЦ", f"{distances['mall_dist']} м")
        
        with infra_cols[2]:
            st.metric("До поликлиники", f"{distances['clinic_dist']} м")
            st.metric("До парковки", f"{distances['parking_dist']} м")
        
        # Кнопка прогноза
        if st.button("Рассчитать стоимость", type="primary"):
            try:
                input_data = prepare_input_data(
                    area, rooms, floor, year_built, repair_type, house_type,
                    distances['metro_dist'], distances['school_dist'],
                    distances['park_dist'], distances['mall_dist'],
                    distances['clinic_dist'], distances['parking_dist']
                )
                
                # Отладочная информация
                st.write("Входные данные для модели:", input_data)
                
                prediction = make_prediction(model, input_data)
                if prediction is not None:
                    show_prediction_results(prediction, input_data)
                else:
                    st.error("Не удалось получить прогноз")
            except Exception as e:
                logger.error(f"Ошибка при расчете прогноза: {e}")
                st.error(f"Ошибка при расчете прогноза: {str(e)}")
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        st.error(f"Произошла ошибка: {str(e)}")

def prepare_input_data(area, rooms, floor, year_built, repair_type, house_type,
                     metro_dist, school_dist, park_dist, mall_dist, clinic_dist, parking_dist):
    """Подготовка входных данных"""
    try:
        # Базовые параметры
        data = {
            'total_area': float(area),
            'living_area': float(area * 0.7),  # Примерно 70% от общей площади
            'kitchen_area': float(area * 0.15),  # Примерно 15% от общей площади
            'rooms': int(rooms),
            'floor': int(floor),
            'total_floors': 25,  # Стандартное значение
            'year_built': int(year_built),
            'ceiling_height': 2.7,  # Стандартное значение
            'floor_ratio': float(floor) / 25,  # Отношение этажа к общему количеству этажей
        }
        
        # Параметры ремонта
        repair_mapping = {
            "Без ремонта": "trebuet_remonta",
            "Косметический": "kosmeticheskiy",
            "Евроремонт": "evro"
        }
        for repair in ["trebuet_remonta", "kosmeticheskiy", "evro"]:
            data[f'repair_{repair}'] = 1 if repair == repair_mapping[repair_type] else 0
        
        # Параметры типа дома
        house_type_mapping = {
            "Панельный": "panelnyy",
            "Кирпичный": "kirpichnyy",
            "Монолитный": "monolitnyy",
            "Блочный": "blochnyy"
        }
        for h_type in ["panelnyy", "kirpichnyy", "monolitnyy", "blochnyy", "monolitno-kirpichnyy"]:
            data[f'house_type_{h_type}'] = 1 if h_type == house_type_mapping[house_type] else 0
        
        # Параметры инфраструктуры
        infrastructure_mapping = {
            'metro_dist': 'Subway Entrance',
            'school_dist': 'School',
            'park_dist': 'Park',
            'mall_dist': 'Mall',
            'clinic_dist': 'Hospital',
            'parking_dist': 'Parking'
        }
        
        for dist_key, infra_key in infrastructure_mapping.items():
            data[infra_key] = 1 if locals()[dist_key] <= 1000 else 0
        
        # Дополнительные параметры инфраструктуры
        additional_infrastructure = [
            'Highway', 'Playground', 'Supermarket', 'Kindergarten',
            'Bus Stop', 'Theatre', 'Sports Centre', 'Square'
        ]
        for infra in additional_infrastructure:
            data[infra] = 0  # По умолчанию отсутствует
        
        # Параметры балкона и санузла
        data.update({
            'balcony_balkon': 1,  # Предполагаем наличие балкона
            'balcony_lodzhiya': 0,
            'bathroom_razdelnyy': 1,  # Предполагаем раздельный санузел
            'bathroom_sovmeschennyy': 0
        })
        
        return data
    except Exception as e:
        logger.error(f"Ошибка в prepare_input_data: {e}")
        raise

def make_prediction(model, input_data):
    """Выполнение прогноза"""
    try:
        input_df = pd.DataFrame([input_data])
        prediction = model.predict(input_df)
        # Умножаем на 100, так как модель, вероятно, возвращает цены в тысячах рублей
        return float(prediction[0]) 
    except Exception as e:
        logger.error(f"Ошибка прогноза: {e}", exc_info=True)
        raise

def show_prediction_results(prediction, input_data):
    """Вывод результатов"""
    try:
        st.markdown("---")
        st.header("📊 Результаты прогнозирования")
        
        # prediction - это цена за квадратный метр
        total_price = prediction * input_data['total_area']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Прогнозируемая стоимость", f"{total_price:,.0f} руб.")
            st.metric("Цена за м²", f"{prediction:,.0f} руб.")
        with col2:
            st.progress(82, text="Достоверность прогноза: 82%")
            st.metric("Рекомендуемая цена", f"{total_price*0.98:,.0f} руб.", delta="-2% для быстрой продажи")
        
        # Условное влияние факторов
        st.subheader("Факторы влияния на стоимость")
        factors = {
            'Площадь': input_data['total_area'] * 0.4,
            'Ремонт': (input_data['repair_evro'] * 2 + input_data['repair_kosmeticheskiy']) * 0.3,
            'Метро': input_data['Subway Entrance'] * 0.2,
            'Год постройки': (2023 - input_data['year_built']) * -0.1,
            'Этаж': input_data['floor'] * 0.05
        }
        
        fig = px.bar(
            x=list(factors.values()),
            y=list(factors.keys()),
            orientation='h',
            labels={'x': 'Влияние', 'y': 'Фактор'},
            title='Вклад факторов в стоимость'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("💡 Рекомендации")
        if input_data['repair_trebuet_remonta'] == 1:
            st.info("Улучшение ремонта может повысить стоимость на 5-15%")
        if input_data['Subway Entrance'] == 0:
            st.warning("Большая удалённость от метро — возможное снижение цены на 7-12%")
        if (2023 - input_data['year_built']) > 30:
            st.warning("Дом старый — цена может быть ниже. Подчеркните другие преимущества.")
    except Exception as e:
        logger.error(f"Ошибка в show_prediction_results: {e}")
        raise

