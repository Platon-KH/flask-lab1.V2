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
    Упрощенная функция сдвига изображения по прямоугольному контуру.
    Сдвигаем весь периметр изображения на shift_pixels пикселей.
    """
    h, w, _ = image_array.shape
    result = image_array.copy()
    
    # Создаем массив пикселей периметра
    perimeter = []
    
    # Верхняя сторона
    for x in range(w):
        perimeter.append(image_array[0, x])
    
    # Правая сторона (без угла)
    for y in range(1, h):
        perimeter.append(image_array[y, w-1])
    
    # Нижняя сторона (без угла)
    for x in range(w-2, -1, -1):
        perimeter.append(image_array[h-1, x])
    
    # Левая сторона (без углов)
    for y in range(h-2, 0, -1):
        perimeter.append(image_array[y, 0])
    
    # Циклический сдвиг периметра
    if shift_pixels > 0:
        shift_pixels = shift_pixels % len(perimeter)
        perimeter = perimeter[-shift_pixels:] + perimeter[:-shift_pixels]
    
    # Восстанавливаем периметр
    idx = 0
    
    # Верхняя сторона
    for x in range(w):
        result[0, x] = perimeter[idx]
        idx += 1
    
    # Правая сторона
    for y in range(1, h):
        result[y, w-1] = perimeter[idx]
        idx += 1
    
    # Нижняя сторона
    for x in range(w-2, -1, -1):
        result[h-1, x] = perimeter[idx]
        idx += 1
    
    # Левая сторона
    for y in range(h-2, 0, -1):
        result[y, 0] = perimeter[idx]
        idx += 1
    
    return result

def create_color_plot(image_array):
    """
    Создаем простой график распределения цветов.
    """
    fig, axes = plt.subplots(3, 1, figsize=(8, 10))
    colors = ['Red', 'Green', 'Blue']
    
    for i in range(3):
        channel = image_array[:, :, i].flatten()
        axes[i].hist(channel, bins=30, color=colors[i].lower(), alpha=0.7, edgecolor='black')
        axes[i].set_title(f'Распределение {colors[i]} канала')
        axes[i].set_xlabel('Интенсивность')
        axes[i].set_ylabel('Частота')
    
    plt.tight_layout()
    
    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=80)
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
        return "Недопустимый формат файла", 400
    
    # Получаем параметр сдвига
    try:
        shift_pixels = int(request.form.get('shift_pixels', 10))
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
        img_array = np.array(img) / 255.0
        
        # Применяем сдвиг
        result_array = shift_image_rectangular(img_array, shift_pixels)
        
        # Создаем графики
        original_plot = create_color_plot(img_array)
        result_plot = create_color_plot(result_array)
        
        # Конвертируем изображения в base64 для отображения
        img = Image.fromarray((img_array * 255).astype(np.uint8))
        result_img = Image.fromarray((result_array * 255).astype(np.uint8))
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        original_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        buffered = io.BytesIO()
        result_img.save(buffered, format="PNG")
        result_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return render_template('result.html',
                             original_image=original_b64,
                             result_image=result_b64,
                             original_plot=original_plot,
                             result_plot=result_plot,
                             shift_pixels=shift_pixels)
    
    except Exception as e:
        return f"Ошибка обработки: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
