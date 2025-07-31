import json
import random
import logging
import os
import datetime
import pytz
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    raise ValueError("Токен не найден! Проверьте файл .env")
QUOTES_FILE = 'quotes.json'

def load_quotes():
    """Загрузка цитат из файла с обработкой ошибок"""
    try:
        if not os.path.exists(QUOTES_FILE):
            raise FileNotFoundError(f"Файл {QUOTES_FILE} не найден")
            
        with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
            quotes = json.load(f)
            
        if not isinstance(quotes, list):
            raise ValueError("Файл должен содержать список цитат")
            
        if len(quotes) == 0:
            logger.warning("Файл с цитатами пуст")
            return ["Пока нет цитат. Попробуйте позже."]
            
        return quotes
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка формата JSON: {e}")
        return ["Ошибка загрузки цитат. Проверьте формат файла."]
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return ["Произошла ошибка при загрузке цитат"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот мотивации.\n\n"
        "Доступные команды:\n"
        "/quote - случайная цитата\n"
        "/daily - подписаться на ежедневную мотивацию\n"
        "/unsubscribe - отписаться от рассылки"
    )

async def send_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка случайной цитаты"""
    try:
        quotes = load_quotes()
        quote = random.choice(quotes)
        await update.message.reply_text(f"⭐️ Ваша цитата:\n\n{quote}")
    except Exception as e:
        logger.error(f"Ошибка при отправке цитаты: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")

async def daily_quote(context: ContextTypes.DEFAULT_TYPE):
    """Отправка ежедневной цитаты"""
    try:
        job = context.job
        quotes = load_quotes()
        quote = random.choice(quotes)
        await context.bot.send_message(job.chat_id, text=f"🌞 Доброе утро! Ваша мотивация:\n\n{quote}")
    except Exception as e:
        logger.error(f"Ошибка в daily_quote: {e}")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подписка на ежедневные цитаты"""
    try:
        chat_id = update.message.chat_id
        # Удаляем старые задания для этого чата
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()
            
        # Создаем новое задание
        context.job_queue.run_daily(
            daily_quote,
            time=datetime.time(hour=7, minute=30, tzinfo=pytz.timezone('Europe/Moscow')),
            chat_id=chat_id,
            name=str(chat_id)
        )
        await update.message.reply_text("✅ Вы подписаны на ежедневные цитаты в 7:30 утра по Москве!")
    except Exception as e:
        logger.error(f"Ошибка при подписке: {e}")
        await update.message.reply_text("⚠️ Не удалось оформить подписку")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отписка от рассылки"""
    try:
        chat_id = update.message.chat_id
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        
        if not current_jobs:
            await update.message.reply_text("ℹ️ Вы не были подписаны на рассылку")
            return
            
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("🔕 Вы отписались от рассылки")
    except Exception as e:
        logger.error(f"Ошибка при отписке: {e}")
        await update.message.reply_text("⚠️ Не удалось отписаться")

def main():
    """Основная функция запуска бота"""
    try:
        # Создаем Application
        application = Application.builder().token(TOKEN).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("quote", send_quote))
        application.add_handler(CommandHandler("daily", subscribe))
        application.add_handler(CommandHandler("unsubscribe", unsubscribe))

        logger.info("Бот запускается...")
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
