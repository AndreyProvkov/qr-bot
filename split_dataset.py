import os
import shutil
import random
import argparse
from pathlib import Path

def split_dataset(source_dir, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """
    Разделяет датасет на train/val/test наборы
    
    Args:
        source_dir: Директория с исходными изображениями
        train_ratio: Доля тренировочных данных (по умолчанию 80%)
        val_ratio: Доля валидационных данных (по умолчанию 10%)
        test_ratio: Доля тестовых данных (по умолчанию 10%)
    """
    # Проверяем существование исходной директории
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Ошибка: директория {source_dir} не существует")
        return
    
    # Создаем директории для train/val/test
    dataset_dir = Path('dataset')
    images_dir = dataset_dir / 'images'
    train_dir = images_dir / 'train'
    val_dir = images_dir / 'val'
    test_dir = images_dir / 'test'
    
    for dir_path in [train_dir, val_dir, test_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Получаем список всех изображений
    image_files = [f for f in source_path.glob('*') if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    
    if not image_files:
        print(f"Ошибка: в директории {source_dir} не найдены изображения")
        return
    
    random.shuffle(image_files)
    
    # Вычисляем количество файлов для каждого набора
    total_files = len(image_files)
    train_size = int(total_files * train_ratio)
    val_size = int(total_files * val_ratio)
    
    # Разделяем файлы
    train_files = image_files[:train_size]
    val_files = image_files[train_size:train_size + val_size]
    test_files = image_files[train_size + val_size:]
    
    # Копируем файлы в соответствующие директории
    for files, dest_dir in [(train_files, train_dir), 
                           (val_files, val_dir), 
                           (test_files, test_dir)]:
        for file in files:
            shutil.copy2(file, dest_dir / file.name)
    
    # Создаем файл с информацией о разделении
    with open(dataset_dir / 'dataset_info.txt', 'w') as f:
        f.write(f"Total images: {total_files}\n")
        f.write(f"Train set: {len(train_files)} images ({len(train_files)/total_files*100:.1f}%)\n")
        f.write(f"Validation set: {len(val_files)} images ({len(val_files)/total_files*100:.1f}%)\n")
        f.write(f"Test set: {len(test_files)} images ({len(test_files)/total_files*100:.1f}%)\n")
    
    print(f"Dataset split completed:")
    print(f"Train: {len(train_files)} images")
    print(f"Validation: {len(val_files)} images")
    print(f"Test: {len(test_files)} images")
    print(f"See dataset_info.txt for details")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split dataset into train/val/test sets')
    parser.add_argument('--source_dir', type=str, required=True, help='Path to source images directory')
    parser.add_argument('--train_ratio', type=float, default=0.8, help='Ratio of training set (default: 0.8)')
    parser.add_argument('--val_ratio', type=float, default=0.1, help='Ratio of validation set (default: 0.1)')
    parser.add_argument('--test_ratio', type=float, default=0.1, help='Ratio of test set (default: 0.1)')
    
    args = parser.parse_args()
    
    # Проверяем, что сумма соотношений равна 1
    if abs(args.train_ratio + args.val_ratio + args.test_ratio - 1.0) > 0.001:
        print("Ошибка: сумма train_ratio, val_ratio и test_ratio должна быть равна 1.0")
        exit(1)
    
    split_dataset(args.source_dir, args.train_ratio, args.val_ratio, args.test_ratio) 