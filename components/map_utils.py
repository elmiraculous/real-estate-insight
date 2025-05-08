import pydeck as pdk
from config import APP_CONFIG
import pandas as pd


def create_mini_map(properties, infra_data=None):
    """Создание мини-карты для главной страницы"""
    # Слой объектов недвижимости (тепловая карта)
    property_layer = pdk.Layer(
        "HeatmapLayer",
        data=properties,
        get_position=["longitude", "latitude"],
        get_weight="price_per_m2",
        opacity=0.8,
        threshold=0.05,
        radius_pixels=30,
    )
    
    layers = [property_layer]
    
    # Слой инфраструктуры (если есть данные)
    if infra_data and 'features' in infra_data:
        infra_df = pd.json_normalize(infra_data['features'])
        infra_layer = pdk.Layer(
            "ScatterplotLayer",
            data=infra_df,
            get_position=["geometry.coordinates[0]", "geometry.coordinates[1]"],
            get_color="[0, 140, 200, 160]",
            get_radius=100,
            pickable=True
        )
        layers.append(infra_layer)
    
    view_state = pdk.ViewState(
        latitude=APP_CONFIG['default_map_center'][0],
        longitude=APP_CONFIG['default_map_center'][1],
        zoom=APP_CONFIG['default_zoom'],
        pitch=0
    )
    
    return pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=layers,
        tooltip={
            "html": "<b>Цена:</b> {price_per_m2} руб./м²",
            "style": {"color": "white"}
        },
        height=400
    )