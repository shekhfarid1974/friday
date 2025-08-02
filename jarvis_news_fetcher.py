import feedparser
from livekit.agents import function_tool

@function_tool
async def get_latest_news(topic: str = "") -> str:
    if not topic:
        topic = "top stories"
    feed_url = f"https://news.google.com/rss/search?q={topic.replace(' ', '+')}&hl=en-BD&gl=BD&ceid=BD:en"
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        return f"⚠️ '{topic}' সম্পর্কিত কোনো খবর পাওয়া যায়নি।"

    result = f"📰 '{topic}' সম্পর্কিত সর্বশেষ খবর:\n\n"
    for entry in feed.entries[:5]:
        result += f"🟢 {entry.title}\n🔗 {entry.link}\n\n"
    return result.strip()
