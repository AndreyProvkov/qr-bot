import os
import shutil
import random
from pathlib import Path

def reduce_dataset(input_dir: str, output_dir: str, train_size: int = 20, val_size: int = 5, test_size: int = 5):
    """Уменьшает размер датасета для быстрого тестирования"""
    # Создаем выходные директории
    splits = ["train", "val", "test"]
    for split in splits:
        os.makedirs(os.path.join(output_dir, split, "labels"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, split, "images"), exist_ok=True)
    
    # Копируем файлы для каждого сплита
    for split, size in zip(splits, [train_size, val_size, test_size]):
        # Получаем список файлов
        images_dir = os.path.join(input_dir, split, "images")
        labels_dir = os.path.join(input_dir, split, "labels")
        
        image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png'))]
        label_files = [f.replace('.jpg', '.txt').replace('.png', '.txt') for f in image_files]
        
        # Выбираем случайные файлы
        selected_indices = random.sample(range(len(image_files)), min(size, len(image_files)))
        
        # Копируем выбранные файлы
        for idx in selected_indices:
            # Копируем изображение
            src_img = os.path.join(images_dir, image_files[idx])
            dst_img = os.path.join(output_dir, split, "images", image_files[idx])
            shutil.copy2(src_img, dst_img)
            
            # Копируем метку
            src_label = os.path.join(labels_dir, label_files[idx])
            dst_label = os.path.join(output_dir, split, "labels", label_files[idx])
            shutil.copy2(src_label, dst_label)
    
    # Создаем dataset.yaml
    yaml_content = f"""path: {os.path.abspath(output_dir)}
train: train/images
val: val/images
test: test/images

# Classes
names:
  0: stamp
  1: text
  2: table
  3: graphic
  4: empty_space
"""
    
    with open(os.path.join(output_dir, "dataset.yaml"), "w") as f:
        f.write(yaml_content)
    
    print(f"Датасет уменьшен и сохранен в {output_dir}")
    print(f"Размеры сплитов: train={train_size}, val={val_size}, test={test_size}")

if __name__ == "__main__":
    reduce_dataset("dataset_yolo", "dataset_yolo_small") 