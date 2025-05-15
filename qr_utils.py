import cv2
import numpy as np
from yolo_detector import YOLODetector
import qrcode
from PIL import Image
import os

def add_qr_to_image(image_path: str, qr_content: str, output_path: str) -> bool:
    """
    Добавляет QR-код на изображение в оптимальном месте
    
    Args:
        image_path: путь к исходному изображению
        qr_content: содержимое QR-кода
        qr_size: размер QR-кода в пикселях
        output_path: путь для сохранения результата
        
    Returns:
        bool: True если QR-код успешно добавлен, False в противном случае
    """
    try:
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            return False
            
        # Инициализируем YOLO детектор
        detector = YOLODetector()
        
        # Получаем детекции объектов
        detections = detector.detect(image)
        
        # Генерируем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем PIL Image в numpy array
        qr_np = np.array(qr_img)
        qr_np = cv2.cvtColor(qr_np, cv2.COLOR_RGB2BGR)
        
        # Находим оптимальное место для размещения QR-кода
        # Пока что просто размещаем в правом нижнем углу
        h, w = image.shape[:2]
        qr_h, qr_w = qr_np.shape[:2]
        
        # Вычисляем координаты для размещения
        x = w - qr_w - 20  # 20 пикселей отступа от края
        y = h - qr_h - 20
        
        # Размещаем QR-код на изображении
        roi = image[y:y+qr_h, x:x+qr_w]
        if roi.shape[:2] == qr_np.shape[:2]:
            # Создаем маску для QR-кода
            mask = cv2.cvtColor(qr_np, cv2.COLOR_BGR2GRAY)
            mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
            mask_inv = cv2.bitwise_not(mask)
            
            # Применяем маску
            img_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
            qr_fg = cv2.bitwise_and(qr_np, qr_np, mask=mask)
            dst = cv2.add(img_bg, qr_fg)
            image[y:y+qr_h, x:x+qr_w] = dst
            
            # Сохраняем результат
            cv2.imwrite(output_path, image)
            return True
            
        return False
        
    except Exception as e:
        print(f"Ошибка при добавлении QR-кода: {str(e)}")
        return False 