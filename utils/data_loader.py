import pandas as pd
import json
import joblib
import os
from pathlib import Path
from config import MODEL_CONFIG
import geopandas as gpd
import logging

logger = logging.getLogger(__name__)

def load_properties():
    """Загрузка данных о недвижимости"""
    file_path = "data/avito_full.csv"
    return pd.read_csv(file_path)

def load_infrastructure():
    """Загрузка данных об инфраструктуре"""
    try:
        file_path = 'data/infrastructure.geojson'
        logger.info(f"Начинаем загрузку файла: {file_path}")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            return None
            
        # Загружаем GeoJSON файл
        logger.info("Загружаем GeoJSON файл...")
        gdf = gpd.read_file(file_path)
        logger.info(f"Файл загружен. Количество объектов: {len(gdf)}")
        logger.info(f"Типы геометрий в файле: {gdf.geometry.geom_type.unique()}")
        
        if gdf.empty:
            logger.error("Загруженный файл не содержит данных")
            return None
            
        # Проверяем наличие необходимых колонок
        if 'type' not in gdf.columns:
            logger.error("В файле отсутствует колонка 'type'")
            return None
            
        if 'geometry' not in gdf.columns:
            logger.error("В файле отсутствует колонка 'geometry'")
            return None
        
        # Преобразуем в словарь по типам инфраструктуры
        infrastructure = {}
        unique_types = gdf['type'].unique()
        logger.info(f"Найдены типы инфраструктуры: {unique_types}")
        
        for infra_type in unique_types:
            logger.info(f"Обработка типа: {infra_type}")
            # Получаем данные для текущего типа инфраструктуры
            infra_data = gdf[gdf['type'] == infra_type].copy()
            logger.info(f"Количество объектов типа {infra_type}: {len(infra_data)}")
            
            # Извлекаем координаты из геометрии
            if 'geometry' in infra_data.columns:
                # Создаем новые колонки для координат
                infra_data['longitude'] = None
                infra_data['latitude'] = None
                
                # Обрабатываем каждую геометрию
                for idx, row in infra_data.iterrows():
                    try:
                        geom = row['geometry']
                        if geom.geom_type == 'Point':
                            infra_data.at[idx, 'longitude'] = float(geom.x)
                            infra_data.at[idx, 'latitude'] = float(geom.y)
                        elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                            infra_data.at[idx, 'longitude'] = float(geom.centroid.x)
                            infra_data.at[idx, 'latitude'] = float(geom.centroid.y)
                        elif geom.geom_type == 'LineString':
                            mid_point = geom.interpolate(0.5, normalized=True)
                            infra_data.at[idx, 'longitude'] = float(mid_point.x)
                            infra_data.at[idx, 'latitude'] = float(mid_point.y)
                        else:
                            logger.warning(f"Неизвестный тип геометрии {geom.geom_type} для объекта {idx}")
                            infra_data.at[idx, 'longitude'] = float(geom.centroid.x)
                            infra_data.at[idx, 'latitude'] = float(geom.centroid.y)
                    except Exception as e:
                        logger.error(f"Ошибка при обработке геометрии {idx}: {e}")
                        continue
                
                # Удаляем строки с отсутствующими координатами
                infra_data = infra_data.dropna(subset=['longitude', 'latitude'])
                
                if not infra_data.empty:
                    # Преобразуем координаты в числовой формат
                    infra_data['longitude'] = pd.to_numeric(infra_data['longitude'], errors='coerce')
                    infra_data['latitude'] = pd.to_numeric(infra_data['latitude'], errors='coerce')
                    
                    # Удаляем строки с некорректными координатами
                    infra_data = infra_data.dropna(subset=['longitude', 'latitude'])
                    
                    infrastructure[infra_type] = infra_data
                    logger.info(f"Добавлено {len(infra_data)} объектов типа {infra_type}")
                else:
                    logger.warning(f"Нет валидных объектов для типа {infra_type}")
        
        if not infrastructure:
            logger.error("Не удалось создать ни одного слоя инфраструктуры")
            return None
            
        logger.info(f"Успешно загружено {len(infrastructure)} типов инфраструктуры")
        return infrastructure
        
    except Exception as e:
        logger.error(f"Ошибка загрузки данных инфраструктуры: {e}", exc_info=True)
        return None
    

def load_model():
    """Загрузка обученной модели"""
    try:
        model = joblib.load(MODEL_CONFIG['price_model'])
        return model
    except Exception as e:
        raise Exception(f"Ошибка загрузки модели: {str(e)}")

