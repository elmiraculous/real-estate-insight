import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from utils.logger import setup_logger

logger = setup_logger(__name__)

def show_analytics_page():
    """Страница с аналитическими графиками"""
    st.title("📊 Аналитика недвижимости")
    st.markdown("---")
    
    try:
        # Загрузка данных
        df = pd.read_csv('data/cleaned_real_estate_data .csv')
        
        # Основные метрики
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Средняя цена за м²", f"{df['price_per_sqm'].mean():,.0f} руб.")
        with col2:
            st.metric("Медианная цена за м²", f"{df['price_per_sqm'].median():,.0f} руб.")
        with col3:
            st.metric("Количество объектов", f"{len(df):,}")
        
        st.markdown("---")
        
        # Графики зависимости цены от инфраструктуры
        st.subheader("📊 Влияние инфраструктуры на стоимость")
        
        # Создаем вкладки для разных типов графиков
        tab1, tab2, tab3 = st.tabs(["Метро", "Школы и детские сады", "Торговые центры и парки"])
        
        with tab1:
            # График зависимости цены от количества станций метро поблизости
            fig = px.scatter(
                df,
                x='Subway Entrance',
                y='price_per_sqm',
                title='Зависимость цены от количества станций метро поблизости',
                labels={
                    'Subway Entrance': 'Количество станций метро',
                    'price_per_sqm': 'Цена за м² (руб.)'
                },
                trendline="ols"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Статистика по количеству станций метро
            metro_stats = df.groupby('Subway Entrance')['price_per_sqm'].agg(['mean', 'count']).round(0)
            metro_stats.columns = ['Средняя цена за м²', 'Количество объектов']
            st.dataframe(metro_stats, use_container_width=True)
        
        with tab2:
            # График зависимости цены от количества школ и детских садов
            col1, col2 = st.columns(2)
            with col1:
                fig_school = px.scatter(
                    df,
                    x='School',
                    y='price_per_sqm',
                    title='Зависимость цены от количества школ',
                    labels={
                        'School': 'Количество школ',
                        'price_per_sqm': 'Цена за м² (руб.)'
                    },
                    trendline="ols"
                )
                st.plotly_chart(fig_school, use_container_width=True)
            
            with col2:
                fig_kindergarten = px.scatter(
                    df,
                    x='Kindergarten',
                    y='price_per_sqm',
                    title='Зависимость цены от количества детских садов',
                    labels={
                        'Kindergarten': 'Количество детских садов',
                        'price_per_sqm': 'Цена за м² (руб.)'
                    },
                    trendline="ols"
                )
                st.plotly_chart(fig_kindergarten, use_container_width=True)
        
        with tab3:
            # График зависимости цены от количества торговых центров и парков
            col1, col2 = st.columns(2)
            with col1:
                fig_mall = px.scatter(
                    df,
                    x='Mall',
                    y='price_per_sqm',
                    title='Зависимость цены от количества торговых центров',
                    labels={
                        'Mall': 'Количество ТЦ',
                        'price_per_sqm': 'Цена за м² (руб.)'
                    },
                    trendline="ols"
                )
                st.plotly_chart(fig_mall, use_container_width=True)
            
            with col2:
                fig_park = px.scatter(
                    df,
                    x='Park',
                    y='price_per_sqm',
                    title='Зависимость цены от количества парков',
                    labels={
                        'Park': 'Количество парков',
                        'price_per_sqm': 'Цена за м² (руб.)'
                    },
                    trendline="ols"
                )
                st.plotly_chart(fig_park, use_container_width=True)
        
        # Корреляционная матрица
        st.markdown("---")
        st.subheader("📊 Корреляция между параметрами")
        
        # Выбираем только числовые колонки для корреляции
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        corr_matrix = df[numeric_cols].corr()
        
        # Создаем тепловую карту корреляций
        fig_corr = px.imshow(
            corr_matrix,
            title='Корреляционная матрица',
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Ошибка на странице аналитики: {e}")
        st.error(f"Произошла ошибка при загрузке данных: {str(e)}")
        st.info("Проверьте наличие и формат файла данных")