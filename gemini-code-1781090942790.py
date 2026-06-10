import os
import sys
import subprocess

# Автоматическая установка openpyxl прямо при запуске, если её нет
try:
    import openpyxl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

import streamlit as st
import pandas as pd
import urllib.parse

# Настройка страницы для мобильных устройств
st.set_page_config(page_title="Курьер-Помощник", layout="centered")

st.title("📦 Курьер-Помощник")

# Инициализация базы данных в памяти
if 'orders' not in st.session_state:
    st.session_state.orders = None

# 1. Загрузка файла
uploaded_file = st.file_uploader("Загрузите Excel/CSV файл с заказами", type=["csv", "xlsx"])

if uploaded_file:
    if st.session_state.orders is None:
        # Читаем файл (поддерживаем и CSV, и Excel)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Добавляем колонки для работы курьера, если их нет в исходном файле
        if 'Статус' not in df.columns:
            df['Статус'] = 'В пути'
        if 'Стоимость доставки' not in df.columns:
            df['Стоимость доставки'] = 0.0
            
        st.session_state.orders = df

# Если файл загружен, показываем интерфейс
if st.session_state.orders is not None:
    df = st.session_state.orders

    # Считаем статистику для верхней панели
    total_orders = len(df)
    delivered = len(df[df['Статус'] == 'Доставлен'])
    total_earned = df['Стоимость доставки'].sum()
    
    st.metric(label="Заработано за день (доставка)", value=f"{total_earned} ₸")
    st.write(f"📊 Выполнено: {delivered} из {total_orders}")
    
    st.markdown("---")
    st.subheader("Список заказов на сегодня:")

    # 2. Вывод списка заказов в виде кнопок
    for index, row in df.iterrows():
        # Цветной индикатор статуса для наглядности
        status_emoji = "⏳" if row['Статус'] == 'В пути' else "✅" if row['Статус'] == 'Доставлен' else "❌" if row['Статус'] == 'Отказ' else "📅"
        
        # Берем реальные названия колонок: ID и Адрес
        button_label = f"{status_emoji} Заказ №{row['ID']} — {row['Адрес']}"
        
        if st.button(button_label, key=f"btn_{index}"):
            st.session_state.selected_order = index

    # 3. Экран детальной информации
    if 'selected_order' in st.session_state:
        idx = st.session_state.selected_order
        order = df.iloc[idx]
        
        st.markdown("---")
        st.subheader(f"🔍 Детали заказа №{order['ID']}")
        
        # Вывод данных из вашей таблицы
        st.write(f"**Клиент:** {order['ФИО']}")
        st.write(f"**Город:** {order['Город']}")
        st.write(f"**Адрес:** {order['Адрес']}")
        st.write(f"**Товары:** {order['Товары']}")
        st.write(f"**Комментарий:** {order['Комментарий']}")
        
        # Кнопка СВЯЗИ (убираем лишние символы из телефона для корректного звонка)
        phone = str(order['Телефон']).replace(" ", "").replace("-", "").replace("'", "")
        st.markdown(f'<a href="tel:{phone}" style="display: inline-block; padding: 12px 20px; background-color: #25D366; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 8px; width: 100%; font-weight: bold;">📞 Позвонить клиенту</a>', unsafe_allow_html=True)
        
        # Кнопка НАВИГАЦИИ (Яндекс.Карты с учетом города и адреса)
        full_address = f"{order['Город']}, {order['Адрес']}"
        address_encoded = urllib.parse.quote(full_address)
        yandex_maps_url = f"https://yandex.ru/maps/?text={address_encoded}"
        st.markdown(f'<a href="{yandex_maps_url}" target="_blank" style="display: inline-block; padding: 12px 20px; background-color: #2196F3; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 8px; width: 100%; margin-top: 10px; font-weight: bold;">🗺️ Открыть в Картах</a>', unsafe_allow_html=True)
        
        st.write("")
        
        # Изменение стоимости доставки и статуса
        new_delivery_cost = st.number_input("Укажите сумму вашей доставки за этот заказ:", value=float(order['Стоимость доставки']), key=f"cost_{idx}")
        df.at[idx, 'Стоимость доставки'] = new_delivery_cost
        
        # Кнопки изменения статуса
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Доставлен", key=f"del_{idx}"):
                df.at[idx, 'Статус'] = 'Доставлен'
                st.session_state.orders = df
                st.rerun()
        with col2:
            if st.button("❌ Отказ", key=f"ref_{idx}"):
                df.at[idx, 'Статус'] = 'Отказ'
                st.session_state.orders = df
                st.rerun()
        with col3:
            if st.button("📅 Перенесен", key=f"post_{idx}"):
                df.at[idx, 'Статус'] = 'Перенесен'
                st.session_state.orders = df
                st.rerun()

    # 4. Выгрузка отчета в конце дня
    st.markdown("---")
    st.subheader("🏁 Завершение смены")
    
    csv_report = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Скачать готовый отчет за день",
        data=csv_report,
        file_name="report_today.csv",
        mime="text/csv"
    )