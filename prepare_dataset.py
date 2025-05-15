import os
import shutil
from pathlib import Path

def prepare_dataset_structure():
    """Создаёт структуру папок для датасета"""
    # Создаём основные папки
    dataset_dir = Path('dataset')
    images_dir = dataset_dir / 'images'
    labels_dir = dataset_dir / 'labels'
    
    # Создаём подпапки для тренировочных и валидационных данных
    for split in ['train', 'val']:
        (images_dir / split).mkdir(parents=True, exist_ok=True)
        (labels_dir / split).mkdir(parents=True, exist_ok=True)
    
    print("Структура датасета создана:")
    print(f"- {images_dir}/train/ - для тренировочных изображений")
    print(f"- {images_dir}/val/ - для валидационных изображений")
    print(f"- {labels_dir}/train/ - для разметки тренировочных изображений")
    print(f"- {labels_dir}/val/ - для разметки валидационных изображений")
    print("\nКлассы для разметки (dataset/classes.txt):")
    print("- stamp (штампы)")
    print("- text (текстовые блоки)")
    print("- table (таблицы)")
    print("- graphic (графические элементы)")

if __name__ == '__main__':
    prepare_dataset_structure() 