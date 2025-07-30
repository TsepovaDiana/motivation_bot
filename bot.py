import json
import random
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater, 
    CommandHandler, 
    CallbackContext,
    MessageHandler,
    filters
)
from dotenv import load_dotenv
import pytz
from datetime import time

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
QUOTES_FILE = 'quotes.json'

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка цитат
def load_quotes():
    with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Клавиатура
def get_keyboard():
    return ReplyKeyboardMarkup(
        [
            ['⭐ Случайная цитата', '🌅 Ежедневно'],
            ['💼 Для работы', '❤️ Для души'],
            ['🌍 Для жизни', '🏆 Для спорта']
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# Команды
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    text = (
        f"Привет, {user.first_name}! Я бот мотивации 🤖\n"
        "Выбери категорию или нажми:\n"
        "/random - случайная цитата\n"
        "/subscribe - подписаться на ежедневную мотивацию\n\n"
        "Используй кнопки для быстрого доступа ⬇️"
    )
    update.message.reply_text(text, reply_markup=get_keyboard())

def send_random_quote(update: Update, context: CallbackContext):
    quotes = load_quotes()
    all_quotes = [quote for category in quotes.values() for quote in category]
    quote = random.choice(all_quotes)
    update.message.reply_text(f"⭐️ Ваша цитата:\n\n{quote}")

def send_quote_by_category(update: Update, context: CallbackContext, category: str):
    quotes = load_quotes()
    if category in quotes:
        quote = random.choice(quotes[category])
        update.message.reply_text(f"📌 {category.capitalize()}:\n\n{quote}")
    else:
        update.message.reply_text("Категория не найдена")

def daily_quote(context: CallbackContext):
    job = context.job
    quotes = load_quotes()
    all_quotes = [quote for category in quotes.values() for quote in category]
    quote = random.choice(all_quotes)
    context.bot.send_message(job.context, text=f"🌞 Доброе утро! Ваша доза мотивации:\n\n{quote}")

def subscribe(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    
    # Удаляем старые задачи
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    
    # Добавляем новую задачу
    context.job_queue.run_daily(
        daily_quote,
        time=time(hour=7, minute=30, tzinfo=pytz.timezone('Europe/Moscow')),
        days=(0, 1, 2, 3, 4, 5, 6),
        context=chat_id,
        name=str(chat_id)
    )
    update.message.reply_text(
        "✅ Вы подписаны на ежедневные цитаты!\n"
        "Буду присылать их каждый день в 7:30 утра по Москве."
    )

def unsubscribe(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if not current_jobs:
        update.message.reply_text("❌ Вы не подписаны на рассылку")
        return
    
    for job in current_jobs:
        job.schedule_removal()
    update.message.reply_text("🔕 Вы отписались от ежедневных цитат")

def button_handler(update: Update, context: CallbackContext):
    text = update.message.text
    if text == '⭐ Случайная цитата':
        send_random_quote(update, context)
    elif text == '🌅 Ежедневно':
        subscribe(update, context)
    elif text == '💼 Для работы':
        send_quote_by_category(update, context, 'work')
    elif text == '❤️ Для души':
        send_quote_by_category(update, context, 'soul')
    elif text == '🌍 Для жизни':
        send_quote_by_category(update, context, 'life')
    elif text == '🏆 Для спорта':
        send_quote_by_category(update, context, 'sport')

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("random", send_random_quote))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Обработчик кнопок
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

    updater.start_polling()
    logger.info("Бот запущен!")
    updater.idle()

if __name__ == '__main__':
    main()
