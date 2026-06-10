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
        
        # Добавляем колонки для работы курьера, если их нет
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
    
    st.metric(label="Заработано за день", value=f"{total_earned} руб.")
    st.write(f"📊 Выполнено: {delivered} из {total_orders}")
    
    st.markdown("---")
    st.subheader("Список заказов на сегодня:")

    # 2. Вывод списка заказов в виде кнопок
    for index, row in df.iterrows():
        # Цветной индикатор статуса для наглядности
        status_emoji = "⏳" if row['Статус'] == 'В пути' else "✅" if row['Статус'] == 'Доставлен' else "❌" if row['Статус'] == 'Отказ' else "📅"
        
        button_label = f"{status_emoji} Заказ №{row['Номер']} — {row['Адрес доставки']}"
        
        if st.button(button_label, key=f"btn_{index}"):
            st.session_state.selected_order = index

    # 3. Экран детальной информации (модальное окно / нижняя панель)
    if 'selected_order' in st.session_state:
        idx = st.session_state.selected_order
        order = df.iloc[idx]
        
        st.markdown("---")
        st.subheader(f"🔍 Детали заказа №{order['Номер']}")
        
        # Вывод данных
        st.write(f"**Клиент:** {order['ФИО']}")
        st.write(f"**Препарат:** {order['Препарат']}")
        st.write(f"**Сумма к оплате:** {order['Сумма']} руб.")
        st.write(f"**Комментарий:** {order['Комментарий']}")
        
        # Кнопка СВЯЗИ (работает на смартфонах)
        phone = str(order['Телефон']).replace(" ", "").replace("-", "")
        st.markdown(f'<a href="tel:{phone}" style="display: inline-block; padding: 10px 20px; background-color: #25D366; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 5px; width: 100%;">📞 Позвонить клиенту</a>', unsafe_allow_html=True)
        
        # Кнопка НАВИГАЦИИ (Яндекс.Карты)
        address_encoded = urllib.parse.quote(str(order['Адрес доставки']))
        yandex_maps_url = f"https://yandex.ru/maps/?text={address_encoded}"
        st.markdown(f'<a href="{yandex_maps_url}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #2196F3; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 5px; width: 100%; margin-top: 10px;">🗺️ Открыть в Картах</a>', unsafe_allow_html=True)
        
        st.write("")
        
        # Изменение стоимости доставки и статуса
        new_delivery_cost = st.number_input("Стоимость доставки (ваш заработок):", value=float(order['Стоимость доставки']), key=f"cost_{idx}")
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
    
    # Переводим измененный DataFrame обратно в Excel/CSV для скачивания
    csv_report = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Скачать отчет за день",
        data=csv_report,
        file_name="report_today.csv",
        mime="text/csv",
        style="width: 100%;"
    )