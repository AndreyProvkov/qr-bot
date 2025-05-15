import torch
import cv2
import numpy as np
from pathlib import Path
import sys
import os

# Получаем путь к корню проекта
PROJECT_ROOT = str(Path(__file__).parent.parent.absolute())

# Добавляем путь к YOLOv5 в sys.path
YOLOV5_PATH = os.path.join(PROJECT_ROOT, 'yolov5')
if YOLOV5_PATH not in sys.path:
    sys.path.insert(0, YOLOV5_PATH)

# Импортируем модули YOLOv5
try:
    sys.path.append(YOLOV5_PATH)
    from yolov5.models.common import DetectMultiBackend
    from yolov5.utils.general import check_img_size, non_max_suppression, scale_boxes
    from yolov5.utils.torch_utils import select_device
    from yolov5.utils.dataloaders import LoadImages
except ImportError as e:
    print(f"Ошибка импорта YOLOv5: {e}")
    print(f"Путь к YOLOv5: {YOLOV5_PATH}")
    print(f"Содержимое директории: {os.listdir(YOLOV5_PATH)}")
    print(f"Путь к моделям: {os.path.join(YOLOV5_PATH, 'models')}")
    print(f"Содержимое директории models: {os.listdir(os.path.join(YOLOV5_PATH, 'models'))}")
    raise

class YOLODetector:
    def __init__(self, weights_path='runs/train/exp4/weights/best.pt', device=''):
        """
        Инициализация детектора YOLOv5
        
        Args:
            weights_path (str): Путь к весам модели
            device (str): Устройство для инференса ('cpu' или 'cuda:0')
        """
        # Преобразуем относительный путь в абсолютный
        if not os.path.isabs(weights_path):
            weights_path = os.path.join(PROJECT_ROOT, weights_path)
            
        self.device = select_device(device)
        self.model = DetectMultiBackend(weights_path, device=self.device)
        self.stride = self.model.stride
        self.names = self.model.names
        self.imgsz = check_img_size((640, 640), s=self.stride)
        
        # Размер QR-кода (в пикселях)
        self.qr_size = 150
        
    def find_empty_space(self, image_path):
        """
        Находит пустое место на чертеже для размещения QR-кода
        
        Args:
            image_path (str): Путь к изображению чертежа
            
        Returns:
            tuple: (x, y) координаты левого верхнего угла для размещения QR-кода
                   или None, если подходящее место не найдено
        """
        # Преобразуем относительный путь в абсолютный
        if not os.path.isabs(image_path):
            image_path = str(Path(__file__).parent.absolute() / image_path)
            
        # Загружаем изображение с помощью OpenCV
        img0 = cv2.imread(image_path)
        if img0 is None:
            print(f"Не удалось загрузить изображение: {image_path}")
            return None
            
        # Изменяем размер изображения для YOLO
        img = cv2.resize(img0, self.imgsz)
        
        # Подготовка изображения
        img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(self.device)
        img = img.float()
        img /= 255
        if len(img.shape) == 3:
            img = img[None]
        
        # Инференс
        pred = self.model(img)
        pred = non_max_suppression(pred, conf_thres=0.1, iou_thres=0.45)
        
        # Получаем размеры оригинального изображения
        height, width = img0.shape[:2]
        
        print("\nНайденные объекты:")
        
        # Ищем пустые места (класс empty_space)
        empty_spaces = []
        for i, det in enumerate(pred):
            if len(det):
                # Масштабируем координаты к размеру оригинального изображения
                det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], img0.shape).round()
                
                for *xyxy, conf, cls in det:
                    class_name = self.names[int(cls)]
                    confidence = float(conf)
                    print(f"- {class_name} (уверенность: {confidence:.2f})")
                    
                    if class_name == 'empty_space':
                        x1, y1, x2, y2 = map(int, xyxy)
                        width = x2 - x1
                        height = y2 - y1
                        area = width * height
                        print(f"  Найдено пустое место: x1={x1}, y1={y1}, x2={x2}, y2={y2}, размер={width}x{height}")
                        empty_spaces.append({
                            'coords': (x1, y1),
                            'area': area,
                            'width': width,
                            'height': height
                        })
        
        if not empty_spaces:
            print("Не найдено пустых мест на изображении.")
            return None
        
        # Выбираем самое большое пустое место
        if empty_spaces:
            best_space = max(empty_spaces, key=lambda x: x['area'])
            x, y = best_space['coords']
            
            # Проверяем, достаточно ли места для QR-кода
            if best_space['width'] >= self.qr_size and best_space['height'] >= self.qr_size:
                print(f"\nВыбрано место размером {best_space['width']}x{best_space['height']} пикселей")
                print(f"Координаты: x={x}, y={y}")
                return (x, y)
            else:
                print(f"\nНайденное место слишком маленькое: {best_space['width']}x{best_space['height']} пикселей")
                return None
        
        return None
    
    def visualize_detection(self, image_path, output_path):
        """
        Визуализирует обнаруженные пустые места на изображении
        
        Args:
            image_path (str): Путь к входному изображению
            output_path (str): Путь для сохранения результата
        """
        # Преобразуем относительные пути в абсолютные
        if not os.path.isabs(image_path):
            image_path = str(Path(__file__).parent.absolute() / image_path)
        if not os.path.isabs(output_path):
            output_path = str(Path(__file__).parent.absolute() / output_path)
            
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            return False
        
        # Находим пустое место
        position = self.find_empty_space(image_path)
        if position is None:
            return False
        
        # Рисуем прямоугольник на месте для QR-кода
        x, y = position
        cv2.rectangle(image, (x, y), (x + self.qr_size, y + self.qr_size), (0, 255, 0), 2)
        
        # Сохраняем результат
        cv2.imwrite(output_path, image)
        return True 