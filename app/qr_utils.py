import qrcode
from PIL import Image
import cv2
import numpy as np
import os
from pdf2image import convert_from_path
from .yolo_detector import YOLODetector
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import logging
import shutil
from PyPDF2 import PdfReader

# Настройка логирования
logger = logging.getLogger(__name__)

def generate_qr_code(content, size=150):
    """Генерирует QR-код с заданным содержимым"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def preprocess_image(image):
    """Предобработка изображения для анализа"""
    # Преобразование в оттенки серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Улучшение контраста
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Размытие для уменьшения шума
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    
    return blurred

def detect_important_regions(image):
    """Обнаружение важных областей на чертеже"""
    # Предобработка
    processed = preprocess_image(image)
    
    # Обнаружение линий (для чертежей это критично)
    edges = cv2.Canny(processed, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=100, maxLineGap=10)
    
    # Создание маски важных областей
    mask = np.zeros_like(image)
    
    # Добавляем линии в маску
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(mask, (x1, y1), (x2, y2), (255, 255, 255), 20)
    
    # Добавляем текст и мелкие детали
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if 100 < cv2.contourArea(contour) < 5000:  # Фильтруем по размеру
            cv2.drawContours(mask, [contour], -1, (255, 255, 255), 5)
    
    # Расширяем маску для безопасности
    kernel = np.ones((20,20), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    return mask

def find_qr_position(image_path):
    """Находит оптимальное место для QR-кода на изображении"""
    # Загружаем изображение
    if image_path.lower().endswith('.pdf'):
        images = convert_from_path(image_path)
        if not images:
            return None
        image = np.array(images[0])
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    else:
        image = cv2.imread(image_path)
        if image is None:
            return None
    
    height, width = image.shape[:2]
    qr_size = 150  # Уменьшенный размер QR-кода
    
    # Получаем маску важных областей
    mask = detect_important_regions(image)
    
    # Определяем зоны для проверки (исключая края чертежа)
    margin = 50  # отступ от края
    positions = [
        (width - qr_size - margin, margin),                    # Правый верхний
        (margin, margin),                                      # Левый верхний
        (margin, height - qr_size - margin),                   # Левый нижний
        (width - qr_size - margin, height - qr_size - margin)  # Правый нижний
    ]
    
    # Выбираем позицию с наименьшим перекрытием важных областей
    best_position = None
    min_overlap = float('inf')
    
    for pos in positions:
        x, y = pos
        # Проверяем, не выходит ли QR-код за пределы изображения
        if x < 0 or y < 0 or x + qr_size > width or y + qr_size > height:
            continue
            
        # Проверяем перекрытие с важными областями
        roi = mask[y:y+qr_size, x:x+qr_size]
        overlap = np.sum(roi) / (qr_size * qr_size * 255)
        
        if overlap < min_overlap:
            min_overlap = overlap
            best_position = pos
    
    return best_position

def process_pdf(pdf_path: str, qr_content_template: str, output_path: str, dpi: int = 300) -> bool:
    """
    Обрабатывает PDF файл, добавляя QR-код на каждую страницу (по одной странице за раз, с YOLOv5)
    Args:
        pdf_path (str): Путь к PDF файлу
        qr_content_template (str): Шаблон содержимого QR-кода (можно добавить номер страницы)
        output_path (str): Путь для сохранения результата
        dpi (int): DPI для конвертации страниц
    Returns:
        bool: True если успешно, False в случае ошибки
    """
    try:
        logger.info(f"Начинаем обработку PDF файла: {pdf_path}")
        num_pages = len(PdfReader(pdf_path).pages)
        logger.info(f"Всего страниц: {num_pages}")
        temp_images = []
        temp_dir = tempfile.mkdtemp(prefix="qr_pdf_")
        logger.info(f"Временная директория: {temp_dir}")
        for i in range(1, num_pages + 1):
            logger.info(f"Обработка страницы {i} из {num_pages}")
            # 1. Конвертируем только одну страницу
            images = convert_from_path(pdf_path, dpi=dpi, first_page=i, last_page=i)
            if not images:
                logger.error(f"Не удалось конвертировать страницу {i}")
                shutil.rmtree(temp_dir)
                return False
            img = images[0]
            temp_img_path = os.path.join(temp_dir, f"temp_page_{i}.png")
            img.save(temp_img_path)
            # 2. Генерируем QR-код с учетом номера страницы
            page_qr_content = qr_content_template + f"\nСтраница: {i} из {num_pages}"
            processed_img_path = os.path.join(temp_dir, f"processed_page_{i}.png")
            # 3. Обрабатываем через YOLOv5 и вставляем QR-код
            ok = add_qr_to_image(temp_img_path, page_qr_content, processed_img_path)
            if not ok:
                logger.error(f"Не удалось добавить QR-код на страницу {i}")
                shutil.rmtree(temp_dir)
                return False
            temp_images.append(processed_img_path)
            os.remove(temp_img_path)
        # 4. Собираем обратно в PDF
        logger.info("Собираем обработанные страницы обратно в PDF...")
        images = [Image.open(p).convert('RGB') for p in temp_images]
        images[0].save(output_path, save_all=True, append_images=images[1:])
        for p in temp_images:
            os.remove(p)
        shutil.rmtree(temp_dir)
        logger.info(f"PDF успешно обработан и сохранен: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обработке PDF: {str(e)}", exc_info=True)
        return False

def create_pdf_from_images(image_paths, output_path, dpi=200):
    """Создает PDF из списка изображений"""
    try:
        logger.info(f"Создание PDF из {len(image_paths)} изображений")
        
        # Открываем первое изображение для получения размеров
        first_image = Image.open(image_paths[0])
        width, height = first_image.size
        logger.info(f"Размеры страницы: {width}x{height}")
        
        # Создаем PDF
        c = canvas.Canvas(output_path, pagesize=(width, height))
        
        # Добавляем каждое изображение как страницу
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"Добавление страницы {i} в PDF...")
            c.drawImage(image_path, 0, 0, width=width, height=height)
            c.showPage()
            
            # Очищаем память
            logger.info("Очистка памяти...")
            import gc
            gc.collect()
            logger.info("Память очищена")
        
        logger.info("Сохранение PDF...")
        c.save()
        logger.info("PDF успешно сохранен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {str(e)}", exc_info=True)
        return False

def add_qr_to_image(image_path, qr_content, output_path):
    """Добавляет QR-код на изображение"""
    # Генерируем QR-код
    qr_img = generate_qr_code(qr_content)
    
    # Инициализируем детектор YOLOv5
    detector = YOLODetector()
    
    # Находим позицию для QR-кода
    position = detector.find_empty_space(image_path)
    if position is None:
        # Если YOLO не нашел место, используем резервный метод
        position = find_qr_position(image_path)
    if position is None:
        return False

    # Открываем исходное изображение
    base_img = Image.open(image_path)
    
    # Изменяем размер QR-кода до нужного
    qr_img = qr_img.resize((150, 150))  # Используем фиксированный размер 150x150
    
    # Добавляем белый фон под QR-код
    white_bg = Image.new('RGB', (150, 150), 'white')
    
    # Вставляем белый фон и QR-код
    x, y = position
    base_img.paste(white_bg, (x, y))
    base_img.paste(qr_img, (x, y))
    
    # Сохраняем результат
    base_img.save(output_path)
    return True 