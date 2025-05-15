from models import init_db, Document, QRCode
from sqlalchemy.orm import sessionmaker
from datetime import datetime

def view_documents():
    """Просмотр всех документов в базе данных"""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n=== Документы ===")
    documents = session.query(Document).all()
    for doc in documents:
        print(f"\nID: {doc.id}")
        print(f"Название: {doc.name}")
        print(f"Версия: {doc.version}")
        print(f"Автор: {doc.author}")
        print(f"Статус: {doc.status}")
        print(f"Дата создания: {doc.created_at}")
        
        # Показываем связанные QR-коды
        if doc.qr_codes:
            print("\nQR-коды:")
            for qr in doc.qr_codes:
                print(f"- ID: {qr.id}")
                print(f"  Позиция: ({qr.x_position}, {qr.y_position})")
                print(f"  Содержимое: {qr.content}")
    
    session.close()

def add_test_data():
    """Добавление тестовых данных"""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Создаем тестовый документ
    doc = Document(
        name="test_drawing.pdf",
        version="1.0",
        author="test_user",
        status="new"
    )
    session.add(doc)
    session.commit()
    
    # Создаем тестовый QR-код
    qr = QRCode(
        document_id=doc.id,
        x_position=100.0,
        y_position=100.0,
        content="Тестовый QR-код"
    )
    session.add(qr)
    session.commit()
    
    print("Тестовые данные добавлены!")
    session.close()

if __name__ == "__main__":
    print("1. Просмотр документов")
    print("2. Добавить тестовые данные")
    choice = input("Выберите действие (1 или 2): ")
    
    if choice == "1":
        view_documents()
    elif choice == "2":
        add_test_data()
    else:
        print("Неверный выбор") 