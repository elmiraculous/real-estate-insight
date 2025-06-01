// Обработчик сообщений от карты
window.addEventListener('message', function(event) {
    if (event.data.type === 'property_selected') {
        // Отправляем данные в Streamlit
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: event.data.data
        }, '*');
    }
}); 