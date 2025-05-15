import sys
from pathlib import Path

# Add the project root directory to Python path
current_dir = str(Path(__file__).resolve().parent.parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
from app.models import Document, QRCode, DocumentHistory, init_db
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from app.config import BOT_TOKEN, SAVE_DIRECTORY
from app import qr_utils
import traceback

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Изменено на DEBUG для более подробного логирования
    handlers=[
        logging.StreamHandler(sys.stdout),  # Вывод в консоль
        logging.FileHandler('bot.log')  # Сохранение в файл
    ]
)
logger = logging.getLogger(__name__)

# Initialize database and create session maker
engine = init_db()
Session = sessionmaker(bind=engine)

# Create save directory if it doesn't exist
SAVE_DIR = os.path.join(os.path.dirname(__file__), SAVE_DIRECTORY)
os.makedirs(SAVE_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Привет! Я QR-код бот. Отправь мне документ (PDF, JPG, JPEG, PNG), '
        'и я добавлю на него QR-код. Для PDF файлов QR-код будет добавлен на каждую страницу.'
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle uploaded documents"""
    document = update.message.document
    file_name = document.file_name
    file_id = document.file_id

    logger.info(f"Получен документ: {file_name} (ID: {file_id})")

    # Check file extension
    allowed_extensions = ('.jpg', '.jpeg', '.png', '.pdf')
    if not file_name.lower().endswith(allowed_extensions):
        await update.message.reply_text(
            f"Извините, я принимаю только файлы в форматах: {', '.join(allowed_extensions)}"
        )
        return

    await update.message.reply_text(
        f"Файл '{file_name}' получен. Начинаю обработку..."
    )

    try:
        # Get file from Telegram
        logger.info("Загрузка файла из Telegram...")
        file = await context.bot.get_file(file_id)
        
        # Save file
        save_path = os.path.join(SAVE_DIR, file_name)
        logger.info(f"Сохранение файла в: {save_path}")
        await file.download_to_drive(save_path)
        logger.info("Файл успешно сохранен")

        # Create database entry
        logger.info("Создание записи в базе данных...")
        session = Session()
        doc = Document(
            name=file_name,
            version="1.0",
            author=str(update.effective_user.id)
        )
        session.add(doc)
        session.commit()
        logger.info(f"Запись создана с ID: {doc.id}")

        # Generate QR code with document info
        qr_content = (
            f"Документ: {file_name}\n"
            f"Версия: {doc.version}\n"
            f"Автор: {doc.author}\n"
            f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"ID: {doc.id}"
        )
        
        # Path for saving result
        output_path = os.path.join(SAVE_DIR, f"qr_{file_name}")
        
        # Process file based on its type
        success = False
        if file_name.lower().endswith('.pdf'):
            logger.info("Начинаю обработку PDF файла...")
            success = qr_utils.process_pdf(save_path, qr_content, output_path)
        else:
            logger.info("Начинаю обработку изображения...")
            success = qr_utils.add_qr_to_image(save_path, qr_content, output_path)
        
        if success:
            # Save QR code information
            logger.info("Сохранение информации о QR-коде...")
            qr = QRCode(
                document_id=doc.id,
                content=qr_content
            )
            session.add(qr)
            session.commit()
            logger.info("Информация о QR-коде сохранена")
            
            # Send processed file
            logger.info("Отправка обработанного файла...")
            await update.message.reply_document(
                document=open(output_path, 'rb'),
                caption="QR-код успешно добавлен на документ!"
            )
            logger.info("Файл успешно отправлен")
        else:
            logger.error("Не удалось найти подходящее место для QR-кода")
            await update.message.reply_text(
                "Не удалось найти подходящее место для QR-кода на документе."
            )

    except Exception as e:
        logger.error("Ошибка при обработке файла:", exc_info=True)
        await update.message.reply_text(
            f"Произошла ошибка при обработке файла: {str(e)}"
        )
    finally:
        session.close()
        # Clean up temporary files
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
                logger.info(f"Временный файл удален: {save_path}")
            if os.path.exists(output_path):
                os.remove(output_path)
                logger.info(f"Временный файл удален: {output_path}")
        except Exception as e:
            logger.error(f"Ошибка при удалении временных файлов: {str(e)}", exc_info=True)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages (when user sends something other than a file)"""
    text = update.message.text
    await update.message.reply_text(
        f"Вы написали: '{text}'. Я понимаю только файлы чертежей или команду /start."
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    if update:
        logger.error(f"Update: {update}")
    if context.error:
        logger.error(f"Error: {context.error}")
        logger.error("Traceback:", exc_info=True)
    
    # Отправляем сообщение об ошибке пользователю
    if update and update.effective_message:
        await update.effective_message.reply_text(
            f"Произошла ошибка: {str(context.error)}\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )

def main() -> None:
    """Start the bot."""
    # Create the application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))

    # Add document handler
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Add text message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
