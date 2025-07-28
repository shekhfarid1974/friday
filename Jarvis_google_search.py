import os
import requests
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool
from datetime import datetime

# পরিবেশ ভ্যারিয়েবল লোড করুন
load_dotenv()

# লগিং কনফিগারেশন
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@function_tool
async def google_search(query: str) -> str:
    logger.info(f"প্রশ্ন পাওয়া গেছে: {query}")

    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        logger.error("API Key বা Search Engine ID অনুপস্থিত।")
        return "Environment variables-এ API Key বা Search Engine ID পাওয়া যায়নি।"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": 3
    }

    logger.info("Google Custom Search API-তে অনুরোধ পাঠানো হচ্ছে...")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        logger.error(f"Google API-তে সমস্যা: {response.status_code} - {response.text}")
        return f"Google Search API-তে ত্রুটি: {response.status_code} - {response.text}"

    data = response.json()
    results = data.get("items", [])

    if not results:
        logger.info("কোনো ফলাফল পাওয়া যায়নি।")
        return "দুঃখিত, কোনো ফলাফল পাওয়া যায়নি।"

    formatted = ""
    logger.info("সার্চ ফলাফল:")
    for i, item in enumerate(results, start=1):
        title = item.get("title", "শিরোনাম পাওয়া যায়নি")
        link = item.get("link", "লিঙ্ক পাওয়া যায়নি")
        snippet = item.get("snippet", "")
        formatted += f"{i}. {title}\n{link}\n{snippet}\n\n"
        logger.info(f"{i}. {title}\n{link}\n{snippet}\n")

    return formatted.strip()

@function_tool
async def get_current_datetime() -> str:
    now = datetime.now()
    logger.info(f"বর্তমান তারিখ ও সময়: {now}")
    return now.isoformat()
