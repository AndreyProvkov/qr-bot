from yolo_detector import YOLODetector
import qr_utils
import os

def test_qr_placement():
    # Пути к файлам
    test_image = 'test_images/Podpyatnik1.jpg'
    detected_image = 'test_images/Podpyatnik1_detected.jpg'
    final_image = 'test_images/Podpyatnik1_with_qr.jpg'
    
    # Создаем детектор
    detector = YOLODetector()
    
    # Выводим информацию о классах
    print("\nДоступные классы в модели:", detector.names)
    
    # Визуализируем обнаруженные пустые места
    success = detector.visualize_detection(test_image, detected_image)
    
    if success:
        print(f"Место для QR-кода найдено. Результат с отметкой сохранен в {detected_image}")
        
        # Создаем тестовый QR-код и размещаем его на изображении
        qr_content = "Тестовый QR-код\nДокумент: Podpyatnik1\nВерсия: 1.0\nДата: 2024-04-30"
        
        if qr_utils.add_qr_to_image(test_image, qr_content, final_image):
            print(f"QR-код успешно добавлен. Результат сохранен в {final_image}")
        else:
            print("Не удалось добавить QR-код на изображение.")
    else:
        print("Тест не удался. Не удалось найти подходящее место для QR-кода.")

if __name__ == '__main__':
    test_qr_placement() 