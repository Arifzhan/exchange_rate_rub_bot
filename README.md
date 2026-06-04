# 💱 Currency Exchange Telegram Bot

Telegram бот для получения актуальных курсов валют с ежедневной автоматической рассылкой.

## ✨ Функционал

- 💵 Курсы USD, EUR, CNY, GBP к RUB
- 🔔 Подписка на ежедневную рассылку (каждый день в 10:00)
- 🎯 Инлайн-кнопки для удобного управления
- 📊 Команда `/stats` для статистики
- 💾 Хранение подписчиков в JSON

## 🛠 Технологии

- Python 3.13
- python-telegram-bot
- aiohttp (асинхронные запросы)
- APScheduler (планировщик)
- ExchangeRate API

## 🚀 Запуск

```bash
git clone https://github.com/ВАШ_НИКНЕЙМ/currency-telegram-bot.git
cd currency-telegram-bot
pip install -r requirements.txt
# Создайте файл .env с BOT_TOKEN
python bot.py