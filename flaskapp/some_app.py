def shift_image_rectangular(image_array, shift_pixels):
    """
    Функция сдвига изображения по прямоугольному контуру.
    Делаем видимый сдвиг периметра.
    """
    h, w = image_array.shape[:2]
    
    # Если изображение в градациях серого
    if len(image_array.shape) == 2:
        result = image_array.copy()
        channels = 1
        result = result.reshape(h, w, 1)
    else:
        result = image_array.copy()
        channels = image_array.shape[2]
    
    # Сдвигаем ВИДИМО - меняем цвет периметра
    color_shift = shift_pixels % 255  # Для видимости изменений
    
    # Верхняя сторона
    for x in range(w):
        if channels == 1:  # Grayscale
            result[0, x, 0] = (result[0, x, 0] + color_shift) % 1.0
        else:  # RGB/RGBA
            result[0, x, 0] = (result[0, x, 0] + color_shift/255) % 1.0  # Красный канал
            if channels >= 3:
                result[0, x, 1] = result[0, x, 1]  # Зеленый без изменений
                result[0, x, 2] = (result[0, x, 2] - color_shift/255) % 1.0  # Синий канал
    
    # Правая сторона
    for y in range(1, h):
        if channels == 1:
            result[y, w-1, 0] = (result[y, w-1, 0] + color_shift) % 1.0
        else:
            result[y, w-1, 0] = result[y, w-1, 0]
            if channels >= 3:
                result[y, w-1, 1] = (result[y, w-1, 1] + color_shift/255) % 1.0
                result[y, w-1, 2] = result[y, w-1, 2]
    
    # Нижняя сторона
    for x in range(w-2, -1, -1):
        if channels == 1:
            result[h-1, x, 0] = (result[h-1, x, 0] + color_shift) % 1.0
        else:
            result[h-1, x, 0] = (result[h-1, x, 0] - color_shift/255) % 1.0
            if channels >= 3:
                result[h-1, x, 1] = result[h-1, x, 1]
                result[h-1, x, 2] = (result[h-1, x, 2] + color_shift/255) % 1.0
    
    # Левая сторона
    for y in range(h-2, 0, -1):
        if channels == 1:
            result[y, 0, 0] = (result[y, 0, 0] + color_shift) % 1.0
        else:
            result[y, 0, 0] = result[y, 0, 0]
            if channels >= 3:
                result[y, 0, 1] = (result[y, 0, 1] - color_shift/255) % 1.0
                result[y, 0, 2] = result[y, 0, 2]
    
    if channels == 1:
        return result.reshape(h, w)
    return result

def create_color_plot(image_array):
    """
    Создаем простой график распределения цветов.
    """
    # Проверяем тип изображения
    if len(image_array.shape) == 2:  # Grayscale
        fig, ax = plt.subplots(figsize=(8, 4))
        channel = (image_array * 255).flatten() if image_array.max() <= 1 else image_array.flatten()
        ax.hist(channel, bins=30, color='gray', alpha=0.7, edgecolor='black')
        ax.set_title('Распределение интенсивности (Grayscale)')
        ax.set_xlabel('Интенсивность (0-255)')
        ax.set_ylabel('Частота')
        ax.set_xlim(0, 255)
    elif image_array.shape[2] == 4:  # RGBA
        fig, axes = plt.subplots(4, 1, figsize=(8, 12))
        colors = ['Red', 'Green', 'Blue', 'Alpha']
        for i in range(4):
            channel = (image_array[:, :, i] * 255).flatten() if image_array.max() <= 1 else image_array[:, :, i].flatten()
            color = colors[i].lower() if i < 3 else 'purple'
            axes[i].hist(channel, bins=30, color=color, alpha=0.7, edgecolor='black')
            axes[i].set_title(f'Распределение {colors[i]} канала')
            axes[i].set_xlabel('Интенсивность (0-255)')
            axes[i].set_ylabel('Частота')
            axes[i].set_xlim(0, 255)
    else:  # RGB
        fig, axes = plt.subplots(3, 1, figsize=(8, 10))
        colors = ['Red', 'Green', 'Blue']
        for i in range(3):
            channel = (image_array[:, :, i] * 255).flatten() if image_array.max() <= 1 else image_array[:, :, i].flatten()
            axes[i].hist(channel, bins=30, color=colors[i].lower(), alpha=0.7, edgecolor='black')
            axes[i].set_title(f'Распределение {colors[i]} канала')
            axes[i].set_xlabel('Интенсивность (0-255)')
            axes[i].set_ylabel('Частота')
            axes[i].set_xlim(0, 255)
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=80)
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.read()).decode('utf-8')
