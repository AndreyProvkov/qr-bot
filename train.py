import os
import torch
from pathlib import Path

def train_yolov5():
    # Путь к конфигурационному файлу датасета
    data_yaml = 'dataset_yolo/dataset.yaml'
    
    # Параметры обучения
    img_size = 640  # размер входного изображения
    batch_size = 4  # уменьшенный размер батча
    epochs = 100  # количество эпох
    weights = 'yolov5s.pt'  # предобученные веса
    
    # Создаем директорию для сохранения результатов
    os.makedirs('runs/train', exist_ok=True)
    
    # Переходим в директорию YOLOv5 и запускаем обучение
    os.chdir('yolov5')
    cmd = f'python train.py --img {img_size} --batch {batch_size} --epochs {epochs} ' \
          f'--data ../{data_yaml} --weights {weights} --project ../runs/train --name exp --device cpu'
    
    # Запускаем обучение
    os.system(cmd)
    
    # Возвращаемся в исходную директорию
    os.chdir('..')

if __name__ == '__main__':
    train_yolov5() 