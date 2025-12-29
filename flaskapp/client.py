import requests
import base64
import json

def test_local():
    """Тестирование локального сервера"""
    print("Тестирование локального сервера Flask...")
    
    # 1. Проверяем главную страницу
    try:
        response = requests.get('http://127.0.0.1:5000/')
        print(f"Главная страница: {response.status_code}")
    except:
        print("Сервер не запущен! Запустите сначала some_app.py")
        return
    
    # 2. Тестируем API
    print("\nТестирование API...")
    
    # Читаем тестовое изображение
    with open('static/image0008.png', 'rb') as f:
        image_data = f.read()
    
    # Подготавливаем данные для отправки
    files = {'image': ('test.png', image_data, 'image/png')}
    data = {'shift_pixels': 20}
    
    try:
        response = requests.post('http://127.0.0.1:5000/process', 
                                files=files, 
                                data=data)
        
        if response.status_code == 200:
            print("✓ API работает корректно")
            print(f"Статус: {response.status_code}")
            
            # Сохраняем результат для просмотра
            with open('test_result.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("✓ Результат сохранен в test_result.html")
        else:
            print(f"✗ Ошибка API: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"✗ Ошибка при тестировании API: {e}")

if __name__ == "__main__":
    test_local()
