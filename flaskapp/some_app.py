import os
import numpy as np
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from PIL import Image
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Создаем папку для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def shift_image_rectangular(image_array, shift_pixels):
    """
    Функция сдвига изображения по прямоугольному контуру.
    Вариант 20: сдвиг по замкнутым прямоугольным составляющим.
    """
    h, w = image_array.shape[:2]
    
    # Если изображение в градациях серого
    if len(image_array.shape) == 2:
        # Конвертируем в RGB для наглядности
        result = np.stack([image_array] * 3, axis=2)
        channels = 3
    else:
        result = image_array.copy()
        channels = image_array.shape[2]
    
    # Определяем количество прямоугольных слоев (контуров)
    layers = min(h, w) // 2
    if layers == 0:
        layers = 1
    
    for layer in range(layers):
        # Координаты текущего прямоугольного контура
        top = layer
        bottom = h - layer - 1
        left = layer
        right = w - layer - 1
        
        # Если прямоугольник выродился в линию или точку, пропускаем
        if bottom <= top or right <= left:
            continue
        
        # Вычисляем периметр текущего контура
        perimeter = []
        positions = []
        
        # Верхняя сторона (слева направо)
        for x in range(left, right + 1):
            perimeter.append(result[top, x].copy())
            positions.append((top, x))
        
        # Правая сторона (сверху вниз, без угла)
        for y in range(top + 1, bottom + 1):
            perimeter.append(result[y, right].copy())
            positions.append((y, right))
        
        # Нижняя сторона (справа налево, без угла)
        for x in range(right - 1, left - 1, -1):
            perimeter.append(result[bottom, x].copy())
            positions.append((bottom, x))
        
        # Левая сторона (снизу вверх, без углов)
        for y in range(bottom - 1, top, -1):
            perimeter.append(result[y, left].copy())
            positions.append((y, left))
        
        # Циклический сдвиг пикселей по контуру
        if len(perimeter) > 0:
            # Вычисляем реальный сдвиг для этого контура
            actual_shift = shift_pixels % len(perimeter)
            if actual_shift > 0:
                # Выполняем сдвиг
                shifted_perimeter = perimeter[-actual_shift:] + perimeter[:-actual_shift]
                
                # Записываем сдвинутые пиксели обратно
                for idx, (y, x) in enumerate(positions):
                    result[y, x] = shifted_perimeter[idx]
    
    # Если изначально было grayscale, возвращаем к одному каналу
    if len(image_array.shape) == 2:
        # Берем только один канал (например, красный) или конвертируем в grayscale
        result = np.mean(result, axis=2)
    
    return result

def create_color_plot(image_array, title_prefix=""):
    """
    Создаем график распределения цветов для изображения.
    """
    # Определяем тип изображения
    if len(image_array.shape) == 2:  # Grayscale
        fig, axes = plt.subplots(1, 1, figsize=(10, 4))
        
        # Нормализуем значения для гистограммы
        if image_array.max() <= 1.0:
            data = (image_array * 255).flatten()
        else:
            data = image_array.flatten()
        
        axes.hist(data, bins=50, color='gray', alpha=0.7, edgecolor='black')
        axes.set_title(f'{title_prefix}Распределение интенсивности (Grayscale)')
        axes.set_xlabel('Интенсивность')
        axes.set_ylabel('Частота')
        axes.grid(True, alpha=0.3)
        
    elif image_array.shape[2] == 4:  # RGBA
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        axes = axes.flatten()
        colors = ['Red', 'Green', 'Blue', 'Alpha']
        color_codes = ['red', 'green', 'blue', 'purple']
        
        for i in range(4):
            channel = image_array[:, :, i]
            if channel.max() <= 1.0:
                data = (channel * 255).flatten()
            else:
                data = channel.flatten()
            
            axes[i].hist(data, bins=50, color=color_codes[i], alpha=0.7, edgecolor='black')
            axes[i].set_title(f'{title_prefix}Канал {colors[i]}')
            axes[i].set_xlabel('Интенсивность')
            axes[i].set_ylabel('Частота')
            axes[i].grid(True, alpha=0.3)
            
    else:  # RGB или другое
        channels = min(3, image_array.shape[2])
        fig, axes = plt.subplots(channels, 1, figsize=(10, 3 * channels))
        
        if channels == 1:
            axes = [axes]
        
        colors = ['Red', 'Green', 'Blue']
        
        for i in range(channels):
            channel = image_array[:, :, i]
            if channel.max() <= 1.0:
                data = (channel * 255).flatten()
            else:
                data = channel.flatten()
            
            axes[i].hist(data, bins=50, color=colors[i].lower(), alpha=0.7, edgecolor='black')
            axes[i].set_title(f'{title_prefix}Канал {colors[i]}')
            axes[i].set_xlabel('Интенсивность')
            axes[i].set_ylabel('Частота')
            axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    # Конвертируем в base64
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    # Проверяем файл
    if 'image' not in request.files:
        return "Файл не выбран", 400
    
    file = request.files['image']
    
    if file.filename == '':
        return "Файл не выбран", 400
    
    if not allowed_file(file.filename):
        return "Недопустимый формат файла (разрешены: png, jpg, jpeg)", 400
    
    # Получаем параметр сдвига
    try:
        shift_pixels = int(request.form.get('shift_pixels', 10))
        if shift_pixels < 1:
            shift_pixels = 1
        elif shift_pixels > 1000:
            shift_pixels = 1000
    except:
        shift_pixels = 10
    
    # Сохраняем оригинальный файл
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Обрабатываем изображение
    try:
        # Открываем изображение
        img = Image.open(filepath)
        
        # Конвертируем в RGB для единообразия
        if img.mode in ('RGBA', 'LA', 'P'):
            # Сохраняем альфа-канал если есть
            if img.mode == 'RGBA':
                img_rgb = img.convert('RGB')
                img_array_original = np.array(img_rgb, dtype=np.float32) / 255.0
                # Для альфа-канала создаем отдельный массив
                img_alpha = np.array(img)[:, :, 3] / 255.0
            else:
                img = img.convert('RGB')
                img_array_original = np.array(img, dtype=np.float32) / 255.0
        elif img.mode == 'L':  # Grayscale
            img_array_original = np.array(img, dtype=np.float32) / 255.0
            # Конвертируем в 3 канала для обработки
            img_array_original = np.stack([img_array_original] * 3, axis=2)
        else:  # RGB
            img_array_original = np.array(img, dtype=np.float32) / 255.0
        
        # Применяем сдвиг
        result_array = shift_image_rectangular(img_array_original, shift_pixels)
        
        # Подготавливаем изображения для отображения
        # Оригинальное изображение (конвертируем обратно в 0-255)
        if img_array_original.max() <= 1.0:
            img_display = Image.fromarray((img_array_original * 255).astype(np.uint8))
        else:
            img_display = Image.fromarray(img_array_original.astype(np.uint8))
        
        # Результат обработки
        if result_array.max() <= 1.0:
            result_display = Image.fromarray((result_array * 255).astype(np.uint8))
        else:
            result_display = Image.fromarray(result_array.astype(np.uint8))
        
        # Создаем графики распределения цветов
        original_plot = create_color_plot(img_array_original, "Оригинал: ")
        result_plot = create_color_plot(result_array, "Результат: ")
        
        # Конвертируем изображения в base64 для отображения в HTML
        buffered = io.BytesIO()
        img_display.save(buffered, format="PNG")
        original_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        buffered = io.BytesIO()
        result_display.save(buffered, format="PNG")
        result_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Удаляем временный файл
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return render_template('result.html',
                             original_image=original_b64,
                             result_image=result_b64,
                             original_plot=original_plot,
                             result_plot=result_plot,
                             shift_pixels=shift_pixels)
    
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if os.path.exists(filepath):
            os.remove(filepath)
        return f"Ошибка обработки: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
