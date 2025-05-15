import os
import subprocess

def train_fast():
    # Путь к конфигурации датасета
    data = 'dataset_yolo_small/dataset.yaml'
    
    # Формируем команду для обучения
    cmd = [
        'python',
        'yolov5/train.py',
        '--img', '640',  # размер изображения
        '--batch', '8',  # уменьшаем размер батча для CPU
        '--epochs', '50',  # уменьшаем количество эпох
        '--data', data,
        '--weights', 'yolov5s.pt',  # используем маленькую модель
        '--cache',  # кэшируем изображения в памяти
        '--device', 'cpu',  # используем CPU
        '--project', 'runs/train',
        '--name', 'fast_train',
        '--exist-ok',  # перезаписываем существующие результаты
        '--patience', '10'  # ранняя остановка если нет улучшений
    ]
    
    # Запускаем обучение
    subprocess.run(cmd)
    
    print("Обучение завершено! Результаты сохранены в runs/train/fast_train")

if __name__ == '__main__':
    train_fast() 