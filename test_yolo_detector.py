from yolo_detector import YOLODetector
import os

def test_detector():
    # Пути к файлам
    test_image = 'test_images/Podpyatnik1.jpg'
    output_image = 'test_images/Podpyatnik1_detected.jpg'
    
    # Создаем детектор
    detector = YOLODetector()
    
    # Выводим информацию о классах
    print("\nДоступные классы в модели:", detector.names)
    
    # Визуализируем обнаруженные пустые места
    success = detector.visualize_detection(test_image, output_image)
    
    if success:
        print(f"Тест успешно завершен. Результат сохранен в {output_image}")
    else:
        print("Тест не удался. Не удалось найти подходящее место для QR-кода.")

if __name__ == '__main__':
    test_detector() 