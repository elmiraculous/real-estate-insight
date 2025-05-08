import pandas as pd
import json

def load_properties():
    """Загрузка данных о недвижимости"""
    file_path = "data/avito_full.csv"
    return pd.read_csv(file_path)

def load_infrastructure():
    """Загрузка данных об инфраструктуре"""
    file_path = 'data/infrastructure.geojson'
    with open(file_path) as f:
        return json.load(f)

