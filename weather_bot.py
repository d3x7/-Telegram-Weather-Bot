#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot  # основная библиотека для телеги
import requests  # для запросов к API
import json  # для работы с JSON
import schedule  # для планирования заданий
import time  # для работы со временем
import threading  # для многопоточности
import pytz  # для работы с часовыми поясами
import datetime  # для работы с датой и временем
from telebot import types  # импортируем типы из telebot
from config import (
    BOT_TOKEN, WEATHER_API_KEY, DEFAULT_CITY, 
    DAILY_FORECAST_TIME, WEATHER_API_URL, WEATHER_STICKERS
)  # импортируем настройки из конфига

# создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

# словарь для хранения юзеров, подписавшихся на рассылку
# структура такая: {id_пользователя: название_города}
subscribed_users = {}

def get_weather(city):
    """
    Функция для получения погоды по названию города
    
    Параметры:
        city (str): название города
        
    Возвращает:
        dict: данные о погоде в виде словаря или None, если город не найден
    """
    try:
        # формируем параметры запроса
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric',  # в Цельсиях
            'lang': 'ru'  # на русском языке
        }
        response = requests.get(WEATHER_API_URL, params=params)
        
        # проверяем успешность запроса
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Что-то пошло не так при получении погоды: {e}")
        return None

def format_weather_message(weather_data):
    """
    Функция для форматирования данных о погоде в красивое сообщение
    
    Параметры:
        weather_data (dict): данные о погоде от API
        
    Возвращает:
        str: отформатированное сообщение о погоде
    """
    if not weather_data:
        return "Упс! Не получилось получить данные о погоде. Попробуй позже или проверь название города."
    
    try:
        # достаем нужные данные из JSON
        city_name = weather_data['name']
        country = weather_data['sys']['country']
        temp = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        description = weather_data['weather'][0]['description']
        weather_main = weather_data['weather'][0]['main']
        humidity = weather_data['main']['humidity']
        pressure = weather_data['main']['pressure']
        wind_speed = weather_data['wind']['speed']
        
        # берем стикер для текущей погоды или дефолтный
        weather_sticker = WEATHER_STICKERS.get(weather_main, '🌍')
        
        # собираем сообщение с эмодзи для красоты
        message = (
            f"{weather_sticker} *Погода в {city_name}, {country}* {weather_sticker}\n\n"
            f"🌡 *Температура:* {temp:.1f}°C\n"
            f"🤔 *Ощущается как:* {feels_like:.1f}°C\n"
            f"📝 *Описание:* {description}\n"
            f"💧 *Влажность:* {humidity}%\n"
            f"🔄 *Давление:* {pressure} гПа\n"
            f"🌬 *Ветер:* {wind_speed} м/с\n"
        )
        return message
    except Exception as e:
        print(f"Ошибка при форматировании погоды: {e}")
        return "Что-то пошло не так при обработке данных погоды. Сорян."

def send_daily_forecast():
    """
    Функция для отправки ежедневного прогноза погоды подписчикам
    Запускается автоматически по расписанию
    """
    moscow_time = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
    print(f"Начинаю рассылку прогнозов в {moscow_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # перебираем всех подписчиков
    for user_id, city in subscribed_users.items():
        try:
            # получаем и форматируем данные
            weather_data = get_weather(city)
            message = format_weather_message(weather_data)
            # добавляем приветствие
            message = f"☀️ *Доброе утро! Вот твой прогноз погоды на сегодня:*\n\n{message}"
            bot.send_message(user_id, message, parse_mode='Markdown')
            print(f"Отправил прогноз юзеру {user_id}")
        except Exception as e:
            print(f"Не получилось отправить прогноз юзеру {user_id}: {e}")
    
    print("Рассылка завершена")

def schedule_checker():
    """
    Функция для проверки расписания в отдельном потоке
    """
    while True:
        schedule.run_pending()  # проверяем и запускаем запланированные задачи
        time.sleep(30)  # спим 30 сек чтобы не грузить процессор

# создаем клавиатуру с кнопками
def get_main_keyboard():
    """
    Создает клавиатуру с кнопками для основного меню
    
    Возвращает:
        InlineKeyboardMarkup: объект клавиатуры
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    get_weather_btn = types.InlineKeyboardButton(
        text="🌤 Узнать погоду", callback_data="get_weather"
    )
    subscribe_btn = types.InlineKeyboardButton(
        text="📆 Подписаться на прогноз", callback_data="subscribe"
    )
    unsubscribe_btn = types.InlineKeyboardButton(
        text="❌ Отписаться от прогноза", callback_data="unsubscribe"
    )
    help_btn = types.InlineKeyboardButton(
        text="❓ Помощь", callback_data="help"
    )
    
    # добавляем кнопки на клавиатуру
    keyboard.add(get_weather_btn, subscribe_btn)
    keyboard.add(unsubscribe_btn, help_btn)
    return keyboard

# обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    """
    Обрабатывает команду /start
    Выводит приветствие и показывает кнопки
    """
    user_name = message.from_user.first_name
    welcome_text = (
        f"👋 Привет, {user_name}!\n\n"
        f"Это мой бот погоды для курсового проекта. С его помощью ты можешь:\n"
        f"• Узнать текущую погоду в любом городе (но я рекомендую Курск 😉)\n"
        f"• Подписаться на ежедневные уведомления о погоде в 9:00 утра\n\n"
        f"Нажимай на кнопки ниже или пиши команды!"
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

# обработчик команды /help
@bot.message_handler(commands=['help'])
def help_command(message):
    """
    Обрабатывает команду /help
    Выводит список команд и инструкцию
    """
    help_text = (
        "*Доступные команды:*\n\n"
        "/start - Запустить бота\n"
        "/help - Показать эту справку\n"
        "/weather - Узнать погоду\n"
        "/subscribe - Подписаться на прогноз\n"
        "/unsubscribe - Отписаться от прогноза\n\n"
        "*Как пользоваться:*\n"
        "1. Чтобы узнать погоду, нажми на кнопку «Узнать погоду» или пиши /weather\n"
        "2. Для подписки на прогноз каждое утро, нажми «Подписаться на прогноз» или пиши /subscribe\n"
        "3. Можешь просто написать название города и я покажу погоду там"
    )
    
    bot.send_message(
        message.chat.id, 
        help_text, 
        parse_mode='Markdown', 
        reply_markup=get_main_keyboard()
    )

# обработчик команды /weather
@bot.message_handler(commands=['weather'])
def weather_command(message):
    """
    Обрабатывает команду /weather
    Спрашивает у пользователя город
    """
    msg = bot.send_message(
        message.chat.id, 
        "🏙 Напиши название города, где хочешь узнать погоду (например, Курск):",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_city_step)

def process_city_step(message):
    """
    Обрабатывает ответ пользователя с названием города
    Отправляет прогноз погоды
    """
    city = message.text.strip()
    # получаем и отправляем погоду
    weather_data = get_weather(city)
    
    if weather_data:
        weather_message = format_weather_message(weather_data)
        bot.send_message(
            message.chat.id, 
            weather_message, 
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id, 
            f"😢 Не могу найти город '{city}'. Проверь правильность написания или попробуй другой город (например, Курск работает точно).",
            reply_markup=get_main_keyboard()
        )

# обработчик команды /subscribe
@bot.message_handler(commands=['subscribe'])
def subscribe_command(message):
    """
    Обрабатывает команду /subscribe
    Спрашивает у пользователя город для подписки
    """
    msg = bot.send_message(
        message.chat.id, 
        "🌆 Напиши название города, для которого хочешь получать ежедневный прогноз погоды (или просто напиши 'Курск' - у нас там самая точная погода):",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_subscription)

def process_subscription(message):
    """
    Обрабатывает ответ пользователя и подписывает на прогноз
    """
    city = message.text.strip()
    user_id = message.from_user.id
    
    # проверяем, существует ли город
    weather_data = get_weather(city)
    
    if weather_data:
        # добавляем юзера в подписчики
        subscribed_users[user_id] = city
        
        bot.send_message(
            message.chat.id, 
            f"✅ Супер! Ты подписался на ежедневный прогноз погоды для города {city}.\n"
            f"Каждое утро в 9:00 по Москве я буду присылать тебе актуальный прогноз!",
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            message.chat.id, 
            f"😢 Не могу найти город '{city}'. Проверь правильность написания или попробуй другой город (кстати, Курск - отличный выбор!).",
            reply_markup=get_main_keyboard()
        )

# обработчик команды /unsubscribe
@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_command(message):
    """
    Обрабатывает команду /unsubscribe
    Отписывает пользователя от прогнозов
    """
    user_id = message.from_user.id
    
    if user_id in subscribed_users:
        city = subscribed_users[user_id]
        del subscribed_users[user_id]  # удаляем юзера из подписчиков
        
        bot.send_message(
            message.chat.id, 
            f"❌ Ты отписался от прогноза погоды для города {city}. Жаль... Если передумаешь, всегда можешь подписаться снова!",
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            message.chat.id, 
            "⚠️ Ты не подписан на прогноз погоды. Нечего отменять 🤷‍♂️",
            reply_markup=get_main_keyboard()
        )

# обработчик всех остальных сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    """
    Обрабатывает текстовые сообщения
    Предполагает, что пользователь ввел название города
    """
    city = message.text.strip()
    weather_data = get_weather(city)
    
    if weather_data:
        weather_message = format_weather_message(weather_data)
        bot.send_message(
            message.chat.id, 
            weather_message, 
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id, 
            f"😢 Не могу найти информацию о погоде для '{city}'.\n"
            f"Проверь правильность написания или воспользуйся командами из /help (попробуй написать 'Курск', это точно работает)",
            reply_markup=get_main_keyboard()
        )

# обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """
    Обрабатывает нажатия на inline-кнопки
    """
    if call.data == "get_weather":
        # запрашиваем город
        msg = bot.send_message(
            call.message.chat.id, 
            "🏙 Напиши название города, где хочешь узнать погоду (например, Курск):"
        )
        bot.register_next_step_handler(msg, process_city_step)
        
    elif call.data == "subscribe":
        # запускаем подписку
        msg = bot.send_message(
            call.message.chat.id, 
            "🌆 Напиши название города для ежедневного прогноза (рекомендую Курск):"
        )
        bot.register_next_step_handler(msg, process_subscription)
        
    elif call.data == "unsubscribe":
        # отписываем пользователя
        unsubscribe_command(call.message)
        
    elif call.data == "help":
        # показываем справку
        help_command(call.message)
    
    # убираем часики с кнопки
    bot.answer_callback_query(call.id)

def main():
    """
    Главная функция запуска бота
    """
    # настраиваем ежедневную отправку погоды в 9:00
    schedule.every().day.at(DAILY_FORECAST_TIME, "Europe/Moscow").do(send_daily_forecast)
    
    # запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=schedule_checker)
    scheduler_thread.daemon = True  # завершится вместе с основным потоком
    scheduler_thread.start()
    
    # запускаем бота
    print("Погодный бот запущен! Нажми Ctrl+C чтобы остановить.")
    try:
        bot.polling(none_stop=True)  # запускаем бесконечный опрос сервера
    except Exception as e:
        print(f"Блин, что-то пошло не так: {e}")
        
if __name__ == "__main__":
    main()  # запускаем главную функцию 