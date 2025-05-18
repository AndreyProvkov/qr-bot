import os
import logging
import cv2
import numpy as np
from PIL import Image
import qrcode
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter
import pytesseract
import tempfile
import shutil
import gc
from .yolo_detector import YOLODetector

# Настройка логирования
logger = logging.getLogger(__name__)

class QrProcessor:
    def __init__(self):
        self.detector = None
        self.loaded = False

    def get_detector(self):
        """Получает или создает экземпляр YOLO детектора"""
        if not self.loaded:
            try:
                self.detector = YOLODetector()
                logger.info("YOLO детектор успешно инициализирован")
                self.loaded = True
            except Exception as e:
                logger.error(f"Ошибка при инициализации YOLO детектора: {str(e)}", exc_info=True)
                raise
        return self.detector

    def extract_text_from_image(self, image):
        """Извлекает текст из изображения с помощью OCR"""
        try:
            # Конвертируем в оттенки серого для лучшего распознавания
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Применяем адаптивную пороговую обработку
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            # Распознаем текст
            text = pytesseract.image_to_string(thresh, lang='rus+eng')
            return text.strip()
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста: {str(e)}", exc_info=True)
            return ""

    def generate_qr_code(self, content, size=150):
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

    def preprocess_image(self, image):
        """Предобработка изображения для анализа"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        return blurred

    def detect_important_regions(self, image):
        """Обнаружение важных областей на чертеже"""
        processed = self.preprocess_image(image)
        edges = cv2.Canny(processed, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=100, maxLineGap=10)

        mask = np.zeros_like(image)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(mask, (x1, y1), (x2, y2), (255, 255, 255), 20)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if 100 < cv2.contourArea(contour) < 5000:
                cv2.drawContours(mask, [contour], -1, (255, 255, 255), 5)

        kernel = np.ones((20, 20), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        return mask

    def find_qr_position(self, image_path):
        """Находит оптимальное место для QR-кода на изображении"""
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
        mask = self.detect_important_regions(image)

        margin = 50  # отступ от края
        positions = [
            (width - qr_size - margin, margin),                    # Правый верхний
            (margin, margin),                                      # Левый верхний
            (margin, height - qr_size - margin),                   # Левый нижний
            (width - qr_size - margin, height - qr_size - margin)  # Правый нижний
        ]

        best_position = None
        min_overlap = float('inf')
        for pos in positions:
            x, y = pos
            if x < 0 or y < 0 or x + qr_size > width or y + qr_size > height:
                continue

            roi = mask[y:y + qr_size, x:x + qr_size]
            overlap = np.sum(roi) / (qr_size * qr_size * 255)

            if overlap < min_overlap:
                min_overlap = overlap
                best_position = pos

        return best_position

    def add_qr_to_image(self, image_path: str, qr_content: str, output_path: str) -> bool:
        """
        Добавляет QR-код на изображение, сохраняя текстовый слой
        """
        try:
            # Загружаем изображение
            if image_path.lower().endswith('.pdf'):
                images = convert_from_path(image_path)
                if not images:
                    logger.error(f"Не удалось загрузить изображение из PDF: {image_path}")
                    return False
                base_img = images[0]
            else:
                base_img = Image.open(image_path)

            # Конвертируем в numpy array для OCR
            img_array = np.array(base_img)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Извлекаем текст с помощью OCR
            page_text = self.extract_text_from_image(img_array)
            
            # Добавляем распознанный текст в содержимое QR-кода
            enhanced_qr_content = f"{qr_content}\n\nРаспознанный текст:\n{page_text[:500]}..."  # Ограничиваем длину текста

            # Генерируем QR-код
            qr_img = self.generate_qr_code(enhanced_qr_content).resize((150, 150))
            
            # Создаем белый фон для QR-кода
            white_bg = Image.new('RGB', (150, 150), 'white')

            # Находим место для QR-кода
            detector = self.get_detector()
            position = detector.find_empty_space(image_path)
            if position is None:
                position = self.find_qr_position(image_path)
            if position is None:
                logger.warning("Не найдено подходящих мест для QR-кода")
                return False

            x, y = position
            width, height = base_img.size

            if x < 0 or y < 0 or x + 150 > width or y + 150 > height:
                logger.warning("QR-код вышел за границы изображения")
                return False

            # Накладываем QR-код
            base_img.paste(white_bg, (x, y))
            base_img.paste(qr_img, (x, y))

            # Сохраняем результат
            base_img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении QR-кода: {str(e)}", exc_info=True)
            return False

    def process_pdf(self, pdf_path: str, qr_content_template: str, output_path: str, dpi: int = 300) -> bool:
        """
        Обрабатывает PDF файл, добавляя QR-код на каждую страницу и сохраняя текстовый слой
        """
        try:
            logger.info(f"Начинаем обработку PDF файла: {pdf_path}")
            
            # Открываем исходный PDF для сохранения текстового слоя
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            num_pages = len(reader.pages)
            logger.info(f"Всего страниц: {num_pages}")

            with tempfile.TemporaryDirectory(prefix="qr_pdf_") as temp_dir:
                processed_images = []

                for i in range(num_pages):
                    logger.info(f"Обработка страницы {i+1} из {num_pages}")
                    
                    # Конвертируем страницу в изображение
                    images = convert_from_path(pdf_path, dpi=dpi, first_page=i+1, last_page=i+1)
                    if not images:
                        logger.error(f"Не удалось конвертировать страницу {i+1}")
                        return False
                    img = images[0]

                    # Сохраняем временное изображение
                    temp_img_path = os.path.join(temp_dir, f"temp_page_{i+1}.png")
                    img.save(temp_img_path, "PNG")

                    # Добавляем QR-код
                    page_qr_content = qr_content_template + f"\nСтраница: {i+1} из {num_pages}"
                    processed_img_path = os.path.join(temp_dir, f"processed_page_{i+1}.png")

                    ok = self.add_qr_to_image(temp_img_path, page_qr_content, processed_img_path)
                    if not ok:
                        logger.error(f"Не удалось добавить QR-код на страницу {i+1}")
                        return False

                    processed_images.append(processed_img_path)

                    # Копируем текстовый слой из исходного PDF
                    writer.add_page(reader.pages[i])

                    del img, temp_img_path, processed_img_path
                    gc.collect()

                # Сохраняем PDF с текстовым слоем
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

                logger.info(f"PDF успешно обработан и сохранен: {output_path}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF: {str(e)}", exc_info=True)
            return False