import os
from dotenv import load_dotenv

# подгружаем данные из .env файла если он есть
load_dotenv()

# основные настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_telegram_bot_token_here')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'your_openweather_api_key_here')
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Курск') # мой родной город :)

# время для отправки ежедневного прогноза (9 утра по Москве)
DAILY_FORECAST_TIME = '09:00'

# API URL для получения погоды
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'

# словарик со стикерами для разной погоды
WEATHER_STICKERS = {
    'Clear': '☀️',  # ясно
    'Clouds': '☁️',  # облачно
    'Rain': '🌧️',  # дождь
    'Drizzle': '🌦️',  # морось
    'Thunderstorm': '⛈️',  # гроза
    'Snow': '❄️',  # снег
    'Mist': '🌫️',  # туман
    'Fog': '🌫️',  # туман
    'Haze': '🌫️',  # мгла
    'Smoke': '🌫️',  # дым
    'Dust': '🌫️',  # пыль
    'Sand': '🌫️',  # песок
    'Ash': '🌫️',  # пепел
    'Squall': '💨',  # шквал
    'Tornado': '🌪️'  # торнадо
} 