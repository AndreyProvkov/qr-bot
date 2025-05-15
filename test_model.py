import os
import subprocess

def test_model():
    # Путь к обученной модели
    weights = 'runs/train/exp3/weights/best.pt'
    
    # Путь к тестовому изображению
    source = 'dataset_yolo/test/images/doc1 (13).jpg'
    
    # Путь к конфигурации датасета
    data = 'dataset_yolo/dataset.yaml'
    
    # Формируем команду для запуска detect.py
    cmd = [
        'python',
        'yolov5/detect.py',
        '--weights', weights,
        '--source', source,
        '--data', data,
        '--conf-thres', '0.1',
        '--save-txt',
        '--save-conf',
        '--project', 'runs/detect',
        '--name', 'exp'
    ]
    
    # Запускаем детекцию
    subprocess.run(cmd)
    
    print("Результаты детекции сохранены в runs/detect/exp")

if __name__ == '__main__':
    test_model() 