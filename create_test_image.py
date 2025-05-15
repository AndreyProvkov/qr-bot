import cv2
import numpy as np

def create_test_drawing():
    # Создаем белое изображение
    img = np.ones((800, 1000, 3), dtype=np.uint8) * 255
    
    # Рисуем рамку чертежа
    cv2.rectangle(img, (50, 50), (950, 750), (0, 0, 0), 2)
    
    # Рисуем штамп в правом нижнем углу
    cv2.rectangle(img, (700, 600), (900, 700), (0, 0, 0), 2)
    cv2.putText(img, "Штамп", (720, 650), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    # Рисуем текст
    cv2.putText(img, "Чертеж детали", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, "Масштаб 1:1", (100, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Рисуем размеры
    cv2.line(img, (200, 200), (400, 200), (0, 0, 0), 1)
    cv2.line(img, (200, 190), (200, 210), (0, 0, 0), 1)
    cv2.line(img, (400, 190), (400, 210), (0, 0, 0), 1)
    cv2.putText(img, "200", (280, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Рисуем деталь
    cv2.rectangle(img, (200, 300), (400, 500), (0, 0, 0), 2)
    
    # Сохраняем изображение
    cv2.imwrite('test_drawing.jpg', img)
    print("Тестовый чертеж создан: test_drawing.jpg")

if __name__ == "__main__":
    create_test_drawing() 