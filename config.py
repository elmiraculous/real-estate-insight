from pathlib import Path
# config.py
MAPBOX_TOKEN = "your-mapbox-token-here"
DATA_DIR = "data/"
MODEL_PATH = "models/price_prediction.pkl"
BASE_DIR = Path(__file__).resolve().parents[1]

DATA_CONFIG = {
    "MAPBOX_TOKEN": MAPBOX_TOKEN,
    "DATA_DIR": DATA_DIR,
    "MODEL_PATH": MODEL_PATH,
    "BASE_DIR": BASE_DIR
}

DATA_DIR = {
    'cleaned_real_estate_data': 'data/properties.csv',
    'infrastructure_data': 'data/infrastructure.geojson'
}


APP_CONFIG = {
    'default_map_center': (55.7887, 49.0719), 
    'default_zoom': 10, 
    'debug': True
}
