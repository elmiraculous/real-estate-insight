import re
import numpy as np
import pandas as pd

# Функция для очистки числовых значений от лишних символов
def clean_numeric(value):
    if isinstance(value, str):
        match = re.search(r"\d+(\.\d+)?", value.replace(',', '.'))
        return float(match.group()) if match else np.nan
    return value

def preprocess_data(df):
    # Перевод названий колонок
    df = df.rename(columns={
        'Позиция': 'position',
        'Категория1': 'category_1',
        'Категория2': 'category_2',
        'Категория3': 'category_3',
        'Категория4': 'type',
        'Заголовок': 'title',
        'Пр.Всего': 'total_price',
        'Пр.Сегод.': 'today_price',
        'Цена': 'price',
        'Пониж.цена': 'price_drop',
        'Продвижения': 'promotion',
        'Время поднятия': 'date',
        'Описание': 'description',
        'Кол-во знак.': 'num_chars',
        'Балк/Лодж': 'balcony_loggia',
        'Санузел': 'bathroom',
        'НазвНовостр': 'new_building_name',
        'Корпус': 'corpus',
        'Тип дома': 'house_type',
        'ГрузЛифт': 'freight_elevator',
        'Отделка': 'finish',
        'Этаж': 'floor',
        'Мебель': 'furniture',
        'ПлощКухни': 'kitchen_area',
        'ЖилПлощ': 'living_area',
        'Кол-воЭтаж': 'num_floors',
        'Кол-воКомн': 'num_rooms',
        'Парковка': 'parking',
        'ПассажЛифт': 'passenger_elevator',
        'СрокСдачи': 'delivery_date',
        'Ремонт': 'renovation',
        'ТипУчастия': 'participation_type',
        'ВысПотол': 'ceiling_height',
        'ТипКомнат': 'room_type',
        'Способ продажи': 'sale_method',
        'Техника': 'appliances',
        'ОбщПлощ': 'total_area',
        'Окна': 'windows',
        'ГодПостр': 'year_built',
        '№ объяв.': 'ad_id',
        'Продавец': 'seller',
        'Широта': 'latitude',
        'Долгота': 'longitude',
        'Адрес': 'address',
        'Республика': 'republic',
        'Город': 'city',
        'Метро1': 'metro_1',
        'Метро2': 'metro_2',
        'Метро3': 'metro_3',
        'Район': 'district',
        'Поселок': 'village',
        'Мкр-н': 'microdistrict',
        'Улица': 'street',
        'Ссылка': 'url',
        'Фото шт.': 'num_photos'
    })

    # Преобразование и очистка числовых данных
    for col in ['ceiling_height', 'living_area', 'total_area', 'kitchen_area', 'price']:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)

    df['price_per_m2'] = df['price'] / df['total_area']
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df[(df['price_per_m2'] > 20000) & (df['price_per_m2'] < 500000)]

    return df
