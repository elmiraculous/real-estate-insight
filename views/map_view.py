import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
from utils.data_loader import load_properties, load_infrastructure
from utils.logger import setup_logger
from utils.preprocess_data import preprocess_data
import streamlit.components.v1 as components

logger = setup_logger(__name__)

def show_map_page():
    """Страница с интерактивной картой недвижимости"""
    st.title("🗺️ Карта недвижимости")
    st.markdown("---")
    
    try:
        # Загрузка данных
        properties = load_properties()
        infrastructure = load_infrastructure()
        
        # Предобработка данных
        properties = preprocess_data(properties)
        
        # Проверяем наличие данных
        if properties.empty:
            st.error("Нет данных для отображения")
            return
            
        # Проверяем наличие необходимых колонок
        required_columns = ['price_per_m2', 'total_area', 'num_rooms', 'house_type', 'year_built', 'renovation', 'latitude', 'longitude']
        missing_columns = [col for col in required_columns if col not in properties.columns]
        if missing_columns:
            st.error(f"Отсутствуют необходимые колонки: {', '.join(missing_columns)}")
            return
        
        # Применяем параметры поиска с главной страницы
        if 'search_params' in st.session_state:
            search_params = st.session_state.search_params
            if search_params['address']:
                properties = properties[properties['address'].str.contains(search_params['address'], case=False, na=False)]
            if search_params['type'] != "Все":
                properties = properties[properties['type'] == search_params['type']]
            if search_params['rooms'] != "Все":
                properties = properties[properties['num_rooms'] == search_params['rooms']]
            # Очищаем параметры поиска после применения
            st.session_state.search_params = None
        
        # Боковая панель с фильтрами
        with st.sidebar:
            st.subheader("🔍 Фильтры")
            
            # Проверяем наличие данных для фильтров
            if not properties.empty:
                # Фильтр по цене
                price_range = st.slider(
                    "Цена за м² (руб.)",
                    min_value=int(properties['price_per_m2'].min()),
                    max_value=int(properties['price_per_m2'].max()),
                    value=(int(properties['price_per_m2'].min()), int(properties['price_per_m2'].max()))
                )
                
                # Фильтр по площади
                area_range = st.slider(
                    "Площадь (м²)",
                    min_value=int(properties['total_area'].min()),
                    max_value=int(properties['total_area'].max()),
                    value=(int(properties['total_area'].min()), int(properties['total_area'].max()))
                )
                
                # Фильтр по количеству комнат
                rooms = st.multiselect(
                    "Количество комнат",
                    options=sorted(properties['num_rooms'].unique()),
                    default=sorted(properties['num_rooms'].unique())
                )
                
                # Фильтр по типу дома
                house_types = st.multiselect(
                    "Тип дома",
                    options=properties['house_type'].unique(),
                    default=properties['house_type'].unique()
                )
                
                # Фильтр по году постройки
                year_range = st.slider(
                    "Год постройки",
                    min_value=int(properties['year_built'].min()),
                    max_value=int(properties['year_built'].max()),
                    value=(int(properties['year_built'].min()), int(properties['year_built'].max()))
                )
                
                # Фильтр по ремонту
                repair_types = st.multiselect(
                    "Состояние ремонта",
                    options=properties['renovation'].unique(),
                    default=properties['renovation'].unique()
                )
                
                st.markdown("---")
                st.subheader("🗺️ Слои карты")
                
                # Настройка видимости слоев инфраструктуры
                if infrastructure:
                    # Создаем словарь для хранения состояния видимости слоев
                    if 'visible_layers' not in st.session_state:
                        st.session_state.visible_layers = {
                            'Kindergarten': True,
                            'School': True,
                            'Mall': True,
                            'Playground': True,
                            'Theatre': True,
                            'Supermarket': True,
                            'Subway Entrance': True,
                            'Bus Stop': True,
                            'Park': True,
                            'Square': True,
                            'Sports Centre': True,
                            'Hospital': True,
                            'Parking': True
                        }
                    
                    # Чекбоксы для каждого типа инфраструктуры
                    for infra_type in sorted(st.session_state.visible_layers.keys()):
                        if infra_type in infrastructure and not infrastructure[infra_type].empty:
                            st.session_state.visible_layers[infra_type] = st.checkbox(
                                f"{infra_type} ({len(infrastructure[infra_type])})",
                                value=st.session_state.visible_layers[infra_type],
                                key=f"layer_{infra_type}"
                            )
            else:
                st.error("Нет данных для отображения фильтров")
                return
        
        # Применение фильтров с учетом пустых значений
        filtered_properties = properties.copy()
        
        # Применяем фильтры только если они не пустые
        if price_range[0] != price_range[1]:
            filtered_properties = filtered_properties[
                (filtered_properties['price_per_m2'] >= price_range[0]) &
                (filtered_properties['price_per_m2'] <= price_range[1])
            ]
            
        if area_range[0] != area_range[1]:
            filtered_properties = filtered_properties[
                (filtered_properties['total_area'] >= area_range[0]) &
                (filtered_properties['total_area'] <= area_range[1])
            ]
            
        if rooms:
            filtered_properties = filtered_properties[filtered_properties['num_rooms'].isin(rooms)]
            
        if house_types:
            filtered_properties = filtered_properties[filtered_properties['house_type'].isin(house_types)]
            
        if year_range[0] != year_range[1]:
            filtered_properties = filtered_properties[
                (filtered_properties['year_built'] >= year_range[0]) &
                (filtered_properties['year_built'] <= year_range[1])
            ]
            
        if repair_types:
            filtered_properties = filtered_properties[filtered_properties['renovation'].isin(repair_types)]
        
        # Инициализация состояния для выбранного объекта
        if 'selected_property' not in st.session_state:
            st.session_state.selected_property = None
        
        # Создание карты
        deck = create_map(filtered_properties, infrastructure)
        
        # Отображаем карту
        st.pydeck_chart(deck)
        
        # Добавляем компонент для обработки кликов
        components.html(
            """
            <script>
                window.addEventListener('message', function(event) {
                    if (event.data.type === 'deck.gl.click') {
                        const object = event.data.object;
                        if (object && object.address) {
                            window.parent.postMessage({
                                type: 'streamlit:setComponentValue',
                                value: object.address
                            }, '*');
                        }
                    }
                });
            </script>
            """,
            height=0
        )
        
        # Добавляем выбор объекта из списка
        st.subheader("🔍 Выберите объект для просмотра деталей")
        if len(filtered_properties) > 0:
            selected_address = st.selectbox(
                "Выберите адрес",
                options=filtered_properties['address'].tolist(),
                key="property_selector",
                index=0 if st.session_state.selected_property is None else 
                    filtered_properties['address'].tolist().index(st.session_state.selected_property)
            )
            
            if selected_address:
                selected_property = filtered_properties[filtered_properties['address'] == selected_address].iloc[0]
                show_property_details(selected_property, filtered_properties)
        
        # Статистика по отфильтрованным объектам
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Найдено объектов", len(filtered_properties))
        with col2:
            avg_price = filtered_properties['price_per_m2'].mean()
            st.metric("Средняя цена за м²", f"{avg_price:,.0f} руб.")
        with col3:
            avg_area = filtered_properties['total_area'].mean()
            st.metric("Средняя площадь", f"{avg_area:.1f} м²")
        
        # Таблица с результатами
        st.subheader("📋 Список объектов")
        if len(filtered_properties) > 0:
            display_properties = filtered_properties[[
                'address', 'total_area', 'num_rooms', 'price_per_m2', 
                'house_type', 'year_built', 'renovation'
            ]].copy()
            
            display_properties.columns = [
                'Адрес', 'Площадь', 'Комнат', 'Цена за м²', 
                'Тип дома', 'Год постройки', 'Ремонт'
            ]
            
            st.dataframe(
                display_properties,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("По выбранным критериям ничего не найдено")
            
    except Exception as e:
        logger.error(f"Ошибка на странице карты: {e}")
        st.error(f"Произошла ошибка при загрузке данных: {str(e)}")
        st.info("Проверьте наличие и формат файлов данных")

def show_property_details(property_data, all_properties):
    """Отображение подробной информации о выбранном объекте"""
    st.markdown("---")
    st.subheader("🏠 Подробная информация об объекте")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Адрес:** {property_data['address']}")
        st.markdown(f"**Площадь:** {property_data['total_area']} м²")
        st.markdown(f"**Количество комнат:** {property_data['num_rooms']}")
        st.markdown(f"**Цена за м²:** {property_data['price_per_m2']:,.0f} руб.")
        st.markdown(f"**Общая стоимость:** {property_data['price_per_m2'] * property_data['total_area']:,.0f} руб.")
        
    with col2:
        st.markdown(f"**Тип дома:** {property_data['house_type']}")
        st.markdown(f"**Год постройки:** {property_data['year_built']}")
        st.markdown(f"**Состояние ремонта:** {property_data['renovation']}")
        if 'floor' in property_data:
            st.markdown(f"**Этаж:** {property_data['floor']}")
        if 'ceiling_height' in property_data:
            st.markdown(f"**Высота потолков:** {property_data['ceiling_height']} м")
    
    # Дополнительная информация
    st.markdown("### 📊 Сравнение с похожими объектами")
    
    # Находим похожие объекты (в том же районе, с похожей площадью)
    similar_properties = all_properties[
        (all_properties['address'].str.contains(property_data['address'].split(',')[0], case=False)) &
        (abs(all_properties['total_area'] - property_data['total_area']) <= 10)
    ]
    
    if len(similar_properties) > 1:
        avg_price = similar_properties['price_per_m2'].mean()
        price_diff = ((property_data['price_per_m2'] - avg_price) / avg_price) * 100
        
        st.metric(
            "Средняя цена в районе",
            f"{avg_price:,.0f} руб./м²",
            delta=f"{price_diff:+.1f}%"
        )
        
        # График распределения цен
        fig = px.histogram(
            similar_properties,
            x='price_per_m2',
            title='Распределение цен в районе',
            labels={'price_per_m2': 'Цена за м²', 'count': 'Количество объектов'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Недостаточно данных для сравнения с похожими объектами")

def create_map(properties, infrastructure):
    """Создание интерактивной карты с точками недвижимости и инфраструктурой"""
    if len(properties) == 0:
        view_state = pdk.ViewState(latitude=55.7887, longitude=49.1221, zoom=11, pitch=0)
        return pdk.Deck(map_style="mapbox://styles/mapbox/streets-v11", initial_view_state=view_state)

    view_state = pdk.ViewState(
        latitude=properties['latitude'].mean(),
        longitude=properties['longitude'].mean(),
        zoom=12,
        pitch=0
    )

    # Слой с объектами недвижимости
    property_layer = pdk.Layer(
        'ScatterplotLayer',
        data=properties,
        get_position='[longitude, latitude]',
        get_radius=50,
        get_fill_color='[255, 0, 0, 160]',
        pickable=True
    )

    # Цветовая схема для инфраструктуры
    infra_colors = {
        'Kindergarten': [255, 165, 0, 160],    # Оранжевый
        'School': [0, 128, 0, 160],            # Зеленый
        'Mall': [128, 0, 128, 160],            # Фиолетовый
        'Playground': [0, 255, 255, 160],      # Голубой
        'Theatre': [255, 192, 203, 160],       # Розовый
        'Supermarket': [255, 255, 0, 160],     # Желтый
        'Subway Entrance': [0, 0, 255, 160],   # Синий
        'Bus Stop': [128, 128, 128, 160],      # Серый
        'Park': [0, 255, 0, 160],              # Ярко-зеленый
        'Square': [255, 215, 0, 160],          # Золотой
        'Sports Centre': [255, 0, 255, 160],   # Пурпурный
        'Hospital': [255, 69, 0, 160],         # Красно-оранжевый
        'Parking': [0, 0, 139, 160]            # Темно-синий
    }

    # Создаем слои для каждого типа инфраструктуры
    infra_layers = []
    for infra_type, color in infra_colors.items():
        if (infra_type in infrastructure and 
            not infrastructure[infra_type].empty and 
            st.session_state.visible_layers.get(infra_type, True)):
            infra_data = infrastructure[infra_type].copy()
            
            # Создаем слой для точек
            point_layer = pdk.Layer(
                'ScatterplotLayer',
                data=infra_data,
                get_position='[longitude, latitude]',
                get_radius=30,
                get_fill_color=color,
                pickable=True,
                name=infra_type
            )
            infra_layers.append(point_layer)

    # Объединяем все слои
    layers = [property_layer] + infra_layers

    # Настраиваем всплывающие подсказки
    tooltip = {
        "html": (
            "<b>{address}</b><br/>"
            "Тип жилья: {type}<br/>"
            "Год постройки: {year_built}<br/>"
            "Комнат: {rooms}<br/>"
            "Этаж: {floor}<br/>"
            "Площадь: {total_area} м²<br/>"
            "Цена за м²: {price_per_m2} руб.<br/>"
            "Общая цена: {price} руб."
        ),
        "style": {
            "backgroundColor": "steelblue",
            "color": "white",
            "padding": "8px",
            "borderRadius": "6px",
            "fontSize": "14px",
            "lineHeight": "1.5"
        }
    }

    # Добавляем легенду
    legend_html = """
    <div style="position: absolute; bottom: 10px; right: 10px; background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
        <h4 style="margin: 0 0 10px 0;">Легенда</h4>
    """
    
    for infra_type, color in infra_colors.items():
        if (infra_type in infrastructure and 
            not infrastructure[infra_type].empty and 
            st.session_state.visible_layers.get(infra_type, True)):
            color_hex = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
            legend_html += f'<div style="margin: 5px 0;"><span style="display: inline-block; width: 15px; height: 15px; background-color: {color_hex}; margin-right: 5px;"></span>{infra_type}</div>'
    
    legend_html += "</div>"

    # Создаем компонент с легендой
    components.html(legend_html, height=0)

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/streets-v11"
    )
