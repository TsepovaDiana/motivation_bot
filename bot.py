import json
import random
import logging
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
        "/daily - подписаться на ежедневную мотивацию"
    )

async def send_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = load_quotes()
    quote = random.choice(quotes)
    await update.message.reply_text(f"⭐️ Ваша цитата:\n\n{quote}")

async def daily_quote(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    quotes = load_quotes()
    quote = random.choice(quotes)
    await context.bot.send_message(job.chat_id, text=f"🌞 Доброе утро! Ваша мотивация:\n\n{quote}")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    context.job_queue.run_daily(
        daily_quote,
        time=datetime.time(hour=7, minute=30),
        chat_id=chat_id,
        name=str(chat_id))
    await update.message.reply_text("✅ Вы подписаны на ежедневные цитаты в 7:30 утра!")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    await update.message.reply_text("🔕 Вы отписались от рассылки")

def main():
    # Создаем Application вместо Updater
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quote", send_quote))
    application.add_handler(CommandHandler("daily", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
