import os
import logging
import cv2
import numpy as np
from PIL import Image
import qrcode
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from .yolo_detector import YOLODetector
import tempfile
import shutil
import gc

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
        Добавляет QR-код на изображение, используя YOLOv5 для определения места размещения
        """
        try:
            if image_path.lower().endswith('.pdf'):
                images = convert_from_path(image_path)
                if not images:
                    logger.error(f"Не удалось загрузить изображение из PDF: {image_path}")
                    return False
                base_img = images[0]
            else:
                base_img = Image.open(image_path)

            width, height = base_img.size

            qr_img = self.generate_qr_code(qr_content).resize((150, 150))

            white_bg = Image.new('RGB', (150, 150), 'white')

            detector = self.get_detector()
            position = detector.find_empty_space(image_path)
            if position is None:
                position = self.find_qr_position(image_path)
            if position is None:
                logger.warning("Не найдено подходящих мест для QR-кода")
                return False

            x, y = position

            if x < 0 or y < 0 or x + 150 > width or y + 150 > height:
                logger.warning("QR-код вышел за границы изображения")
                return False

            base_img.paste(white_bg, (x, y))
            base_img.paste(qr_img, (x, y))

            base_img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении QR-кода: {str(e)}", exc_info=True)
            return False

    def process_pdf(self, pdf_path: str, qr_content_template: str, output_path: str, dpi: int = 300) -> bool:
        """
        Обрабатывает PDF файл, добавляя QR-код на каждую страницу
        """
        try:
            logger.info(f"Начинаем обработку PDF файла: {pdf_path}")
            num_pages = len(PdfReader(pdf_path).pages)
            logger.info(f"Всего страниц: {num_pages}")

            with tempfile.TemporaryDirectory(prefix="qr_pdf_") as temp_dir:
                processed_images = []

                for i in range(1, num_pages + 1):
                    logger.info(f"Обработка страницы {i} из {num_pages}")
                    images = convert_from_path(pdf_path, dpi=dpi, first_page=i, last_page=i)
                    if not images:
                        logger.error(f"Не удалось конвертировать страницу {i}")
                        return False
                    img = images[0]

                    temp_img_path = os.path.join(temp_dir, f"temp_page_{i}.png")
                    img.save(temp_img_path, "PNG")

                    page_qr_content = qr_content_template + f"\nСтраница: {i} из {num_pages}"
                    processed_img_path = os.path.join(temp_dir, f"processed_page_{i}.png")

                    ok = self.add_qr_to_image(temp_img_path, page_qr_content, processed_img_path)
                    if not ok:
                        logger.error(f"Не удалось добавить QR-код на страницу {i}")
                        return False

                    processed_images.append(processed_img_path)

                    del img, temp_img_path, processed_img_path
                    gc.collect()

                logger.info("Собираем обработанные страницы обратно в PDF...")
                images = [Image.open(p).convert('RGB') for p in processed_images]
                images[0].save(output_path, save_all=True, append_images=images[1:])

                logger.info(f"PDF успешно обработан и сохранен: {output_path}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF: {str(e)}", exc_info=True)
            return False