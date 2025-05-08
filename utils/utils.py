import pandas as pd
import geopandas as gpd
import joblib

def load_model(path="model/model.pkl"):
    return joblib.load(path)

def load_infrastructure(path="data/infrastructure.geojson"):
    return gpd.read_file(path)

def load_avito(path="data/avito_kazan.csv"):
    return gpd.read_file(path)


