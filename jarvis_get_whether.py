import os
import requests
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool  # ✅ Correct decorator
from langchain.tools import tool

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_current_city():
    try:
        response = requests.get("https://ipinfo.io  ", timeout=5)
        data = response.json()
        return data.get("city", "Unknown")
    except Exception as e:
        return "Unknown"

@tool
async def get_weather(city: str = "") -> str:

    """
    Gives current weather information for a given city.

    Use this tool when the user asks about weather, rain, temperature, humidity, or wind.
    If no city is given, detect city automatically.

    Example prompts:
    - "আজকের আবহাওয়া কেমন?"
    - "Weather বলুন Bangalore এর"
    - "মুম্বাইতে বৃষ্টি হবে কি?"
    """


    
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        logger.error("OpenWeather API key অনুপস্থিত।")
        return "Environment variables এ OpenWeather API key পাওয়া যায়নি।"

    if not city:
        city = get_current_city()

    logger.info(f"শহরের জন্য weather fetch করা হচ্ছে: {city}")
    url = "https://api.openweathermap.org/data/2.5/weather  "
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logger.error(f"OpenWeather API তে error হয়েছে: {response.status_code} - {response.text}")
            return f"Error: {city} এর জন্য weather fetch করা যায়নি। দয়া করে city name চেক করুন।"

        data = response.json()
        weather = data["weather"][0]["description"].title()
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        result = (f"Weather in {city}:\n"
                  f"- Condition: {weather}\n"
                  f"- Temperature: {temperature}°C\n"
                  f"- Humidity: {humidity}%\n"
                  f"- Wind Speed: {wind_speed} m/s")

        logger.info(f"Weather result: \n{result}")
        return result

    except Exception as e:
        logger.exception(f"Weather fetch করার সময় exception হয়েছে: {e}")
        return "Weather fetch করার সময় একটি error হয়েছে"