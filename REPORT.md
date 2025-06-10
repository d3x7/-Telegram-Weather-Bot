# Отчет о разработке Telegram-бота для прогноза погоды

## 1. Введение

Для курсового проекта был разработан Telegram-бот, который позволяет узнавать текущую погоду в любом городе (особенно хорошо работает с Курском) и отправляет ежедневные прогнозы подписчикам в 9:00 утра. Бот создан на языке Python с использованием библиотеки pyTelegramBotAPI и сервиса OpenWeatherMap.

## 2. Структура проекта

Проект состоит из следующих файлов:
- `weather_bot.py` - основной файл с кодом бота
- `config.py` - файл с настройками и константами
- `requirements.txt` - файл с зависимостями для установки

## 3. Описание работы кода

### 3.1. Настройки и конфигурация

Для удобства все настройки вынесены в отдельный файл `config.py`, который загружается в основной код. Это позволяет легко менять параметры без правки основного кода:

```python
import os
from dotenv import load_dotenv

# подгружаем данные из .env файла если он есть
load_dotenv()

# основные настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_telegram_bot_token_here')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'your_openweather_api_key_here')
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Курск') # мой родной город :)
```

### 3.2. Получение погоды

Для получения данных о погоде создана функция `get_weather()`, которая отправляет запрос к API OpenWeatherMap:

```python
def get_weather(city):
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
```

Эта функция принимает название города и возвращает JSON с данными о погоде или `None`, если город не найден. В параметрах запроса указано:
- `units=metric` - чтобы температура была в градусах Цельсия
- `lang=ru` - чтобы описание погоды было на русском языке

### 3.3. Форматирование сообщения

После получения данных, они преобразуются в читабельный вид с помощью функции `format_weather_message()`:

```python
def format_weather_message(weather_data):
    # ... обработка данных ...
    
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
```

Функция извлекает из JSON нужные данные (название города, температуру, описание погоды и т.д.) и создает сообщение с эмодзи, чтобы информация была наглядной и красивой.

### 3.4. Ежедневная отправка прогноза

Для автоматической отправки прогноза в 9:00 утра используется библиотека `schedule` и многопоточность:

```python
def send_daily_forecast():
    """
    Функция для отправки ежедневного прогноза погоды подписчикам
    Запускается автоматически по расписанию
    """
    # ... отправка прогнозов ...

def schedule_checker():
    """
    Функция для проверки расписания в отдельном потоке
    """
    while True:
        schedule.run_pending()  # проверяем и запускаем запланированные задачи
        time.sleep(30)  # спим 30 сек чтобы не грузить процессор

# В функции main():
schedule.every().day.at(DAILY_FORECAST_TIME, "Europe/Moscow").do(send_daily_forecast)
scheduler_thread = threading.Thread(target=schedule_checker)
scheduler_thread.daemon = True
scheduler_thread.start()
```

### 3.5. Команды бота

Бот понимает несколько команд:
- `/start` - запуск бота и приветствие
- `/help` - показ справки и списка команд
- `/weather` - запрос погоды в указанном городе
- `/subscribe` - подписка на ежедневный прогноз
- `/unsubscribe` - отписка от прогноза

Пример обработчика команды `/weather`:

```python
@bot.message_handler(commands=['weather'])
def weather_command(message):
    msg = bot.send_message(
        message.chat.id, 
        "🏙 Напиши название города, где хочешь узнать погоду (например, Курск):"
    )
    bot.register_next_step_handler(msg, process_city_step)

def process_city_step(message):
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
            f"😢 Не могу найти город '{city}'. Проверь правильность написания или попробуй другой город (например, Курск работает точно)."
        )
```

### 3.6. Интерфейс бота

Для удобства пользователей добавлены кнопки с основными командами:

```python
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    get_weather_btn = types.InlineKeyboardButton(
        text="🌤 Узнать погоду", callback_data="get_weather"
    )
    # ... другие кнопки ...
    
    keyboard.add(get_weather_btn, subscribe_btn)
    # ... добавление кнопок ...
    return keyboard
```

Нажатия на кнопки обрабатываются в функции `callback_handler`:

```python
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "get_weather":
        # запрашиваем город
        msg = bot.send_message(
            call.message.chat.id, 
            "🏙 Напиши название города, где хочешь узнать погоду (например, Курск):"
        )
        bot.register_next_step_handler(msg, process_city_step)
    # ... обработка других кнопок ...
```

## 4. Система подписок

В боте есть система подписок, позволяющая получать прогноз каждое утро. Подписки хранятся в словаре `subscribed_users`, где ключ - ID пользователя, а значение - название города:

```python
# словарь для хранения юзеров, подписавшихся на рассылку
subscribed_users = {}
```

Пользователь может подписаться через команду `/subscribe` или кнопку, и отписаться через `/unsubscribe` или соответствующую кнопку.

## 5. Запуск бота

Бот запускается из функции `main()`, которая настраивает расписание и запускает обработку сообщений:

```python
def main():
    # настраиваем ежедневную отправку погоды в 9:00
    schedule.every().day.at(DAILY_FORECAST_TIME, "Europe/Moscow").do(send_daily_forecast)
    
    # запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=schedule_checker)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # запускаем бота
    print("Погодный бот запущен! Нажми Ctrl+C чтобы остановить.")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Блин, что-то пошло не так: {e}")
```

## 6. Вывод

Созданный Telegram-бот отвечает всем поставленным требованиям:
- Написан на Python
- Отправляет прогноз погоды в 9:00 утра
- Имеет нужные команды (/start, /help, /weather и другие)
- Обрабатывает текстовые сообщения от пользователя
- Имеет удобный интерфейс с эмодзи и кнопками
- По умолчанию работает с городом Курск

Самой интересной частью реализации была работа с многопоточностью - это позволило боту одновременно общаться с пользователями и отправлять запланированные сообщения.

В будущем я планирую доработать бота, добавив:
- Прогноз на несколько дней вперед
- Сохранение подписок в базу данных (сейчас они теряются при перезапуске)
- Уведомления о резком изменении погоды
- Возможность выбора языка (хотя русский и так крутой)

## 7. Источники

1. Документация Telegram Bot API: https://core.telegram.org/bots/api
2. Документация pyTelegramBotAPI: https://pypi.org/project/pyTelegramBotAPI/
3. OpenWeatherMap API: https://openweathermap.org/api 