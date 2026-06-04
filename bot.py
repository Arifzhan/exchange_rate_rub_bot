from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import aiohttp
from datetime import datetime
import os
import json
import asyncio
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Файл для хранения подписчиков
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    """Загружает список подписчиков из файла"""
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_subscribers(subscribers):
    """Сохраняет список подписчиков в файл"""
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(list(subscribers), f)

async def get_rates():
    """Получение курсов валют"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            async with session.get(url) as resp:
                data = await resp.json()
                rates = data['rates']
                
                usd_rub = rates.get('RUB', 85.0)
                cny_rub = rates.get('CNY', 11.5)
                gbp_rub = rates.get('GBP', 100.0)
                
                async with session.get("https://api.exchangerate-api.com/v4/latest/EUR") as resp2:
                    data_eur = await resp2.json()
                    eur_rub = data_eur['rates'].get('RUB', 95.0)
                
                return {
                    'USD': round(usd_rub, 2),
                    'EUR': round(eur_rub, 2),
                    'CNY': round(cny_rub, 2),
                    'GBP': round(gbp_rub, 2),
                    'updated': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                }
    except Exception as e:
        print(f"Ошибка API: {e}")
        return {
            'USD': 85.0, 'EUR': 95.0, 'CNY': 11.5, 'GBP': 105.0,
            'updated': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }

def get_keyboard():
    """Главная клавиатура"""
    keyboard = [
        [InlineKeyboardButton("💵 USD", callback_data="usd"),
         InlineKeyboardButton("💶 EUR", callback_data="eur")],
        [InlineKeyboardButton("🇨🇳 CNY", callback_data="cny"),
         InlineKeyboardButton("🇬🇧 GBP", callback_data="gbp")],
        [InlineKeyboardButton("📊 Все курсы", callback_data="all")],
        [InlineKeyboardButton("🔔 Подписаться", callback_data="subscribe"),
         InlineKeyboardButton("🔕 Отписаться", callback_data="unsubscribe")],
        [InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💱 Привет! Я бот курсов валют\n\n"
        "📌 Что я умею:\n"
        "• Показываю курсы USD, EUR, CNY, GBP\n"
        "• Могу присылать курсы каждый день в 10:00\n\n"
        "🔔 Нажмите 'Подписаться' чтобы получать ежедневную рассылку\n\n"
        "Или используйте команды:\n"
        "/usd, /eur, /cny, /all",
        reply_markup=get_keyboard()
    )

async def usd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rates = await get_rates()
    await update.message.reply_text(
        f"💵 USD/RUB: {rates['USD']} ₽\n🕐 {rates['updated']}",
        reply_markup=get_keyboard()
    )

async def eur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rates = await get_rates()
    await update.message.reply_text(
        f"💶 EUR/RUB: {rates['EUR']} ₽\n🕐 {rates['updated']}",
        reply_markup=get_keyboard()
    )

async def cny(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rates = await get_rates()
    await update.message.reply_text(
        f"🇨🇳 CNY/RUB: {rates['CNY']} ₽\n🕐 {rates['updated']}",
        reply_markup=get_keyboard()
    )

async def all_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rates = await get_rates()
    text = (f"💰 *Курсы к рублю*\n\n"
            f"💵 USD: {rates['USD']} ₽\n"
            f"💶 EUR: {rates['EUR']} ₽\n"
            f"🇨🇳 CNY: {rates['CNY']} ₽\n"
            f"🇬🇧 GBP: {rates['GBP']} ₽\n\n"
            f"_🕐 {rates['updated']}_")
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    rates = await get_rates()
    data = query.data
    user_id = query.from_user.id
    subscribers = load_subscribers()
    
    if data == "subscribe":
        if user_id not in subscribers:
            subscribers.add(user_id)
            save_subscribers(subscribers)
            text = "✅ Вы подписались на ежедневную рассылку!\nКурсы будут приходить каждый день в 10:00"
        else:
            text = "ℹ️ Вы уже подписаны на рассылку"
        await query.edit_message_text(
            f"{text}\n\n🕐 {rates['updated']}",
            reply_markup=get_keyboard()
        )
        return
    
    elif data == "unsubscribe":
        if user_id in subscribers:
            subscribers.discard(user_id)
            save_subscribers(subscribers)
            text = "❌ Вы отписались от рассылки"
        else:
            text = "ℹ️ Вы и так не подписаны"
        await query.edit_message_text(
            f"{text}\n\n🕐 {rates['updated']}",
            reply_markup=get_keyboard()
        )
        return
    
    elif data == "refresh":
        text = "🔄 Курсы обновлены"
        await query.edit_message_text(
            f"{text}\n\n🕐 {rates['updated']}",
            reply_markup=get_keyboard()
        )
        return
    
    texts = {
        "usd": f"💵 USD/RUB: {rates['USD']} ₽",
        "eur": f"💶 EUR/RUB: {rates['EUR']} ₽",
        "cny": f"🇨🇳 CNY/RUB: {rates['CNY']} ₽",
        "gbp": f"🇬🇧 GBP/RUB: {rates['GBP']} ₽",
        "all": (f"💰 Все курсы:\n\n"
                f"💵 USD: {rates['USD']} ₽\n"
                f"💶 EUR: {rates['EUR']} ₽\n"
                f"🇨🇳 CNY: {rates['CNY']} ₽\n"
                f"🇬🇧 GBP: {rates['GBP']} ₽")
    }
    
    text = texts.get(data, "❌ Ошибка")
    await query.edit_message_text(
        f"{text}\n\n🕐 {rates['updated']}",
        reply_markup=get_keyboard()
    )

async def daily_newsletter():
    """Функция ежедневной рассылки"""
    subscribers = load_subscribers()
    if not subscribers:
        print("Нет подписчиков для рассылки")
        return
    
    rates = await get_rates()
    
    message = (
        "📊 *Ежедневный курс валют*\n\n"
        f"💵 USD: {rates['USD']} ₽\n"
        f"💶 EUR: {rates['EUR']} ₽\n"
        f"🇨🇳 CNY: {rates['CNY']} ₽\n"
        f"🇬🇧 GBP: {rates['GBP']} ₽\n\n"
        f"🕐 {rates['updated']}\n\n"
        "Чтобы отписаться, нажмите 🔕 Отписаться в боте"
    )
    
    # Создаём временное приложение для отправки сообщений
    app = Application.builder().token(BOT_TOKEN).build()
    await app.initialize()
    
    success_count = 0
    for user_id in subscribers:
        try:
            await app.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=get_keyboard()
            )
            success_count += 1
            await asyncio.sleep(0.05)  # Небольшая задержка чтобы не заблокировали
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")
            if "Forbidden" in str(e) or "chat not found" in str(e):
                subscribers.discard(user_id)
                save_subscribers(subscribers)
    
    await app.shutdown()
    print(f"📨 Рассылка отправлена {success_count} подписчикам")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    subscribers = load_subscribers()
    await update.message.reply_text(
        f"📊 Статистика бота:\n\n"
        f"👥 Подписчиков: {len(subscribers)}\n"
        f"🕐 Последнее обновление: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usd", usd))
    app.add_handler(CommandHandler("eur", eur))
    app.add_handler(CommandHandler("cny", cny))
    app.add_handler(CommandHandler("all", all_currencies))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Настройка планировщика для рассылки
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_newsletter, 'cron', hour=10, minute=0)
    scheduler.start()
    print("✅ Планировщик рассылки запущен (каждый день в 10:00)")
    
    print("✅ Бот успешно запущен!")
    print("📱 Откройте Telegram и найдите своего бота")
    print("🛑 Нажмите Ctrl+C для остановки\n")
    
    # Запускаем бота
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())