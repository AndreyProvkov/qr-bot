import json
import os
import shutil
from pathlib import Path
from PIL import Image

# Mapping of class names to YOLO class IDs
CLASS_MAPPING = {
    "stamp": 0,
    "text": 1,
    "table": 2,
    "graphic": 3,
    "empty_space": 4
}

def convert_bbox_to_yolo(bbox, img_width, img_height):
    """Convert bounding box coordinates to YOLO format (normalized x_center, y_center, width, height)"""
    x = bbox["x"]
    y = bbox["y"]
    width = bbox["width"]
    height = bbox["height"]
    
    # Calculate center coordinates
    x_center = x + width / 2
    y_center = y + height / 2
    
    # Normalize coordinates
    x_center = x_center / img_width
    y_center = y_center / img_height
    width = width / img_width
    height = height / img_height
    
    # Ensure coordinates are within [0, 1]
    x_center = max(0, min(1, x_center))
    y_center = max(0, min(1, y_center))
    width = max(0, min(1, width))
    height = max(0, min(1, height))
    
    return [x_center, y_center, width, height]

def process_via_annotation(regions, img_width, img_height):
    """Process VIA annotations and convert them to YOLO format"""
    yolo_annotations = []
    
    for region in regions:
        shape_attrs = region["shape_attributes"]
        region_attrs = region["region_attributes"]
        
        # Get class ID
        class_name = region_attrs.get("type", "").lower()
        if not class_name or class_name not in CLASS_MAPPING:
            print(f"Warning: Unknown class {class_name}")
            continue
            
        class_id = CLASS_MAPPING[class_name]
        
        # Convert coordinates based on shape type
        if shape_attrs["name"] == "rect":
            coords = convert_bbox_to_yolo(shape_attrs, img_width, img_height)
        else:
            print(f"Warning: Unsupported shape type {shape_attrs['name']}")
            continue
        
        # Format: class_id x_center y_center width height
        yolo_line = f"{class_id} {' '.join(map(str, coords))}"
        yolo_annotations.append(yolo_line)
    
    return yolo_annotations

def get_image_dimensions(img_path):
    """Get image width and height using PIL"""
    try:
        with Image.open(img_path) as img:
            return img.width, img.height
    except Exception as e:
        print(f"Error getting dimensions for {img_path}: {str(e)}")
        return None

def convert_dataset():
    # Пути к директориям
    input_dir = 'dataset'
    output_dir = 'dataset_yolo'
    
    # Создаем выходную директорию
    os.makedirs(output_dir, exist_ok=True)
    
    # Обрабатываем каждый сплит
    splits = ["train", "val", "test"]
    for split in splits:
        print(f"\nProcessing {split} split...")
        
        # Создаем директории для YOLO формата
        os.makedirs(os.path.join(output_dir, split, "labels"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, split, "images"), exist_ok=True)
        
        # Читаем аннотации для текущего сплита
        annotations_file = os.path.join(input_dir, "annotations", split, "annotations.json")
        if not os.path.exists(annotations_file):
            print(f"Warning: Annotations file not found: {annotations_file}")
            continue
            
        with open(annotations_file, 'r', encoding='utf-8') as f:
            try:
                annotations = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error: Could not parse {annotations_file}: {str(e)}")
                continue
        
        # Обрабатываем каждое изображение
        for img_id, img_data in annotations.items():
            filename = img_data.get("filename")
            if not filename:
                print(f"Warning: No filename in annotation {img_id}")
                continue
            
            # Получаем путь к изображению
            img_path = os.path.join(input_dir, "images", split, filename)
            if not os.path.exists(img_path):
                print(f"Warning: Image not found: {img_path}")
                continue
            
            # Получаем размеры изображения
            dimensions = get_image_dimensions(img_path)
            if not dimensions:
                continue
            img_width, img_height = dimensions
            
            # Конвертируем аннотации
            yolo_annotations = process_via_annotation(img_data.get("regions", []), img_width, img_height)
            
            if not yolo_annotations:
                print(f"Warning: No valid annotations found for {filename}")
                continue
            
            # Записываем YOLO аннотации
            label_filename = os.path.splitext(filename)[0] + ".txt"
            with open(os.path.join(output_dir, split, "labels", label_filename), "w") as f:
                f.write("\n".join(yolo_annotations))
            
            # Копируем изображение
            dst_img = os.path.join(output_dir, split, "images", filename)
            shutil.copy2(img_path, dst_img)
            print(f"Processed {filename}")
    
    # Создаем dataset.yaml
    yaml_content = f"""path: {os.path.abspath(output_dir)}  # dataset root dir
train: train/images  # train images
val: val/images  # val images
test: test/images  # test images

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
    
    print(f"\nКонвертация завершена! Данные сохранены в {output_dir}")

if __name__ == '__main__':
    convert_dataset() 