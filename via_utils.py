import os
import json
import shutil
from pathlib import Path

def setup_via_environment():
    """Настройка окружения для работы с VIA"""
    # Создаем необходимые директории
    os.makedirs('dataset/images', exist_ok=True)
    os.makedirs('dataset/annotations', exist_ok=True)
    
    # Копируем конфигурацию VIA
    config_path = Path('dataset/via_config.json')
    if not config_path.exists():
        print("Ошибка: файл конфигурации не найден")
        return False
    
    print("Окружение VIA настроено успешно")
    print("\nИнструкции по использованию:")
    print("1. Откройте via.html в браузере")
    print("2. Нажмите 'Load' и выберите файл конфигурации: dataset/via_config.json")
    print("3. Начните разметку изображений")
    print("4. Сохраняйте аннотации в dataset/annotations/")
    return True

def convert_via_to_yolo(via_json_path, output_dir):
    """Конвертация аннотаций из формата VIA в YOLO"""
    with open(via_json_path, 'r') as f:
        data = json.load(f)
    
    # Создаем директорию для YOLO аннотаций
    os.makedirs(output_dir, exist_ok=True)
    
    # Словарь для соответствия классов
    class_map = {
        "stamp": 0,
        "text": 1,
        "table": 2,
        "graphic": 3,
        "empty_space": 4
    }
    
    for image_id, image_data in data.items():
        if '_via_img_metadata' in image_id:
            continue
            
        filename = image_data['filename']
        regions = image_data.get('regions', [])
        
        # Создаем файл аннотаций для YOLO
        txt_filename = os.path.splitext(filename)[0] + '.txt'
        txt_path = os.path.join(output_dir, txt_filename)
        
        with open(txt_path, 'w') as f:
            for region in regions:
                shape = region['shape_attributes']
                class_name = region['region_attributes']['class']
                class_id = class_map[class_name]
                
                # Конвертируем координаты в формат YOLO
                x = shape['x']
                y = shape['y']
                width = shape['width']
                height = shape['height']
                
                # Нормализуем координаты
                x_center = (x + width/2) / image_data['size'][0]
                y_center = (y + height/2) / image_data['size'][1]
                width_norm = width / image_data['size'][0]
                height_norm = height / image_data['size'][1]
                
                # Записываем в файл
                f.write(f"{class_id} {x_center} {y_center} {width_norm} {height_norm}\n")
    
    print(f"Аннотации успешно конвертированы в формат YOLO и сохранены в {output_dir}")

if __name__ == "__main__":
    setup_via_environment() 