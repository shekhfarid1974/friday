import os
import requests
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool  # ✅ সঠিক ডেকোরেটর

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_city_by_ip() -> str:
    try:
        logger.info("IP থেকে শহর সনাক্ত করার চেষ্টা করা হচ্ছে")
        ip_info = requests.get("https://ipapi.co/json/").json()
        city = ip_info.get("city")
        if city:
            logger.info(f"IP থেকে শহর সনাক্ত হয়েছে: {city}")
            return city
        else:
            logger.warning("শহর সনাক্ত করা যায়নি, ডিফল্ট 'Dhaka' ব্যবহার করা হচ্ছে।")
            return "Dhaka"
    except Exception as e:
        logger.error(f"IP থেকে শহর সনাক্ত করতে সমস্যা হয়েছে: {e}")
        return "Dhaka"

@function_tool
async def get_weather(city: str = "") -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        logger.error("OpenWeather API key পাওয়া যায়নি।")
        return "Environment variables-এ OpenWeather API key সেট করা হয়নি।"

    if not city:
        city = detect_city_by_ip()

    logger.info(f"{city} শহরের জন্য আবহাওয়া খোঁজা হচ্ছে।")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logger.error(f"OpenWeather API তে সমস্যা: {response.status_code} - {response.text}")
            return f"ত্রুটি: {city} শহরের জন্য আবহাওয়া পাওয়া যায়নি। দয়া করে শহরের নাম যাচাই করুন।"

        data = response.json()
        weather = data["weather"][0]["description"].title()
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        result = (f"{city} শহরের আবহাওয়া:\n"
                  f"- আবহাওয়া: {weather}\n"
                  f"- তাপমাত্রা: {temperature}°C\n"
                  f"- আর্দ্রতা: {humidity}%\n"
                  f"- বাতাসের গতি: {wind_speed} m/s")

        logger.info(f"আবহাওয়ার ফলাফল: \n{result}")
        return result

    except Exception as e:
        logger.exception(f"আবহাওয়া খোঁজার সময় একটি সমস্যা হয়েছে: {e}")
        return "আবহাওয়া খোঁজার সময় একটি ত্রুটি হয়েছে।"
