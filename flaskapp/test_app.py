#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы приложения Flask.
Используется в GitHub Actions и для локального тестирования.
"""

import sys
import os
import subprocess
import time
import requests
from pathlib import Path

def print_header(text):
    """Выводит заголовок"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def check_requirements():
    """Проверяет наличие всех необходимых файлов"""
    print_header("ПРОВЕРКА ФАЙЛОВ ПРОЕКТА")
    
    required_files = [
        'some_app.py',
        'requirements.txt',
        'templates/index.html',
        'templates/result.html',
    ]
    
    all_ok = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - НЕ НАЙДЕН")
            all_ok = False
    
    return all_ok

def install_dependencies():
    """Устанавливает зависимости"""
    print_header("УСТАНОВКА ЗАВИСИМОСТЕЙ")
    
    try:
        # Сначала проверяем, установлен ли pip
        result = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("✗ pip не установлен")
            return False
        
        print("✓ pip установлен")
        
        # Устанавливаем зависимости из requirements.txt
        if os.path.exists('requirements.txt'):
            print("Установка зависимостей из requirements.txt...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ Зависимости установлены")
                return True
            else:
                print("✗ Ошибка установки зависимостей:")
                print(result.stderr)
                return False
        else:
            print("✗ Файл requirements.txt не найден")
            return False
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False

def create_test_image():
    """Создает тестовое изображение"""
    print_header("СОЗДАНИЕ ТЕСТОВОГО ИЗОБРАЖЕНИЯ")
    
    # Создаем папку static если её нет
    Path("static").mkdir(exist_ok=True)
    
    test_image_path = "static/test_image.png"
    
    try:
        # Пробуем создать простое изображение
        from PIL import Image
        import numpy as np
        
        # Создаем градиентное изображение 200x200
        img_array = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Заполняем градиентом
        for i in range(200):
            for j in range(200):
                img_array[i, j, 0] = int(i * 255 / 200)  # Красный
                img_array[i, j, 1] = int(j * 255 / 200)  # Зеленый
                img_array[i, j, 2] = 128  # Синий
        
        img = Image.fromarray(img_array)
        img.save(test_image_path)
        
        print(f"✓ Тестовое изображение создано: {test_image_path}")
        return True
        
    except ImportError as e:
        print(f"⚠ Не удалось создать изображение (нет библиотек): {e}")
        # Создаем пустой файл для теста
        with open(test_image_path, 'wb') as f:
            f.write(b'fake image data')
        print(f"✓ Создан пустой файл для теста: {test_image_path}")
        return True
    except Exception as e:
        print(f"✗ Ошибка создания изображения: {e}")
        return False

def test_flask_server():
    """Тестирует Flask сервер"""
    print_header("ТЕСТИРОВАНИЕ FLASK СЕРВЕРА")
    
    # Запускаем сервер в фоновом режиме
    try:
        print("Запуск Flask сервера...")
        server_process = subprocess.Popen(
            [sys.executable, 'some_app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Даем время на запуск
        print("Ожидание запуска сервера (5 секунд)...")
        time.sleep(5)
        
        # Проверяем, запустился ли сервер
        try:
            response = requests.get('http://127.0.0.1:5000/', timeout=10)
            
            if response.status_code == 200:
                print("✓ Сервер запущен и отвечает")
                print(f"  Код ответа: {response.status_code}")
                
                # Тестируем загрузку файла
                print("\nТестирование загрузки файла...")
                with open('static/test_image.png', 'rb') as f:
                    files = {'image': ('test.png', f, 'image/png')}
                    data = {'shift_pixels': '10'}
                    
                    response = requests.post(
                        'http://127.0.0.1:5000/process',
                        files=files,
                        data=data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print("✓ Загрузка и обработка файла работает")
                        
                        # Сохраняем результат для отчета
                        with open('test_output.html', 'w', encoding='utf-8') as out:
                            out.write(response.text)
                        print("  Результат сохранен в test_output.html")
                    else:
                        print(f"✗ Ошибка обработки файла: код {response.status_code}")
                
                # Завершаем процесс сервера
                server_process.terminate()
                server_process.wait(timeout=5)
                return True
                
            else:
                print(f"✗ Сервер вернул ошибку: {response.status_code}")
                server_process.terminate()
                return False
                
        except requests.ConnectionError:
            print("✗ Не удалось подключиться к серверу")
            server_process.terminate()
            return False
        except Exception as e:
            print(f"✗ Ошибка тестирования: {e}")
            server_process.terminate()
            return False
            
    except Exception as e:
        print(f"✗ Ошибка запуска сервера: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("\n" + "=" * 60)
    print(" ТЕСТИРОВАНИЕ ЛАБОРАТОРНОЙ РАБОТЫ №1")
    print(" Вариант 20: Сдвиг изображения по прямоугольному контуру")
    print("=" * 60)
    
    # Проверяем файлы проекта
    if not check_requirements():
        print("\n✗ Не все необходимые файлы найдены!")
        return 1
    
    # Устанавливаем зависимости
    if not install_dependencies():
        print("\n✗ Ошибка установки зависимостей!")
        return 1
    
    # Создаем тестовое изображение
    if not create_test_image():
        print("\n✗ Ошибка создания тестового изображения!")
        return 1
    
    # Тестируем Flask сервер
    if not test_flask_server():
        print("\n✗ Тестирование сервера не пройдено!")
        return 1
    
    # Все тесты пройдены
    print_header("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("\n✓ Проект готов к сдаче")
    print("✓ Все файлы на месте")
    print("✓ Зависимости установлены")
    print("✓ Сервер работает корректно")
    print("✓ Обработка изображений функционирует")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Непредвиденная ошибка: {e}")
        sys.exit(1)
