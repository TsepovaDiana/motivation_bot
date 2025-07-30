import json
import random
import logging
from dotenv import load_dotenv
import os
import datetime  # Добавлен отсутствующий импорт
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
load_dotenv()
# Конфигурация
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    raise ValueError("Токен не найден! Проверьте файл .env")
QUOTES_FILE = 'quotes.json'

def load_quotes():
    with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот мотивации.\n"
        "Используй команды:\n"
        "/start - приветствие\n"
        "/quote - случайная цитата\n"
        "/daily - подписаться на ежедневную мотивацию\n"
        "/unsubscribe - отписаться от рассылки"  # Добавлена информация о новой команде
    )

async def send_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quotes = load_quotes()
        quote = random.choice(quotes)
        await update.message.reply_text(f"⭐️ Ваша цитата:\n\n{quote}")
    except Exception as e:
        logger.error(f"Ошибка при отправке цитаты: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при загрузке цитат")

async def daily_quote(context: ContextTypes.DEFAULT_TYPE):
    try:
        job = context.job
        quotes = load_quotes()
        quote = random.choice(quotes)
        await context.bot.send_message(job.chat_id, text=f"🌞 Доброе утро! Ваша мотивация:\n\n{quote}")
    except Exception as e:
        logger.error(f"Ошибка в daily_quote: {e}")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.message.chat_id
        context.job_queue.run_daily(
            daily_quote,
            time=datetime.time(hour=7, minute=30),
            chat_id=chat_id,
            name=str(chat_id))
        await update.message.reply_text("✅ Вы подписаны на ежедневные цитаты в 7:30 утра!")
    except Exception as e:
        logger.error(f"Ошибка при подписке: {e}")
        await update.message.reply_text("⚠️ Не удалось оформить подписку")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("quote", send_quote))
        application.add_handler(CommandHandler("daily", subscribe))
        application.add_handler(CommandHandler("unsubscribe", unsubscribe))

        logger.info("Бот запускается...")
        application.run_polling()
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")

if __name__ == '__main__':
    main()
