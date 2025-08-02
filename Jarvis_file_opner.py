import os
import subprocess
import sys
import logging
from fuzzywuzzy import process
from livekit.agents import function_tool
import asyncio

try:
    import pygetwindow as gw
except ImportError:
    gw = None

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow ইনস্টল করা নেই")
        return False

    await asyncio.sleep(1.5)
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            logger.info(f"🪟 ফোকাস করা হয়েছে: {window.title}")
            return True
    logger.warning("⚠ ফোকাস করার মতো কোনো উইন্ডো পাওয়া যায়নি।")
    return False


async def index_files(base_dirs):
    file_index = []
    for base_dir in base_dirs:
        for root, dirs, files in os.walk(base_dir):
            for d in dirs:
                file_index.append({
                    "name": d,
                    "path": os.path.join(root, d),
                    "type": "folder"
                })
            for f in files:
                file_index.append({
                    "name": f,
                    "path": os.path.join(root, f),
                    "type": "file"
                })
    logger.info(f"✅ {len(file_index)} ফাইল ও ফোল্ডার ইনডেক্স করা হয়েছে: {base_dirs}")
    return file_index


async def search_file(query, index):
    choices = [item["name"] for item in index if item["type"] == "file"]
    if not choices:
        logger.warning("⚠ মিলানোর জন্য কোনো ফাইল পাওয়া যায়নি।")
        return None

    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 '{query}' এর জন্য সবচেয়ে কাছাকাছি মিল: '{best_match}' (স্কোর: {score})")
    if score > 70:
        for item in index:
            if item["name"] == best_match:
                return item
    return None


async def search_item(name, index, item_type):
    matches = [item for item in index if item["type"] == item_type and name.lower() in item["name"].lower()]
    return matches[0] if matches else None


async def open_file(item):
    try:
        logger.info(f"📂 ফাইল খোলা হচ্ছে: {item['path']}")
        if os.name == 'nt':
            subprocess.Popen(["start", "", item["path"]], shell=True)
        else:
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', item["path"]])

        try:
            await asyncio.wait_for(focus_window(item["name"]), timeout=3)
        except asyncio.TimeoutError:
            logger.warning(f"⚠ ফোকাস করার চেষ্টা timeout হয়েছে: {item['name']}")
        return f"✅ ফাইল ওপেন হয়েছে: {item['name']}"
    except Exception as e:
        logger.error(f"❌ ফাইল খোলার সময় ত্রুটি: {e}")
        return f"❌ ফাইল খোলা যায়নি। {e}"


async def open_folder(path):
    logger.info(f"📁 ফোল্ডার খোলা হচ্ছে: {path}")
    try:
        if os.name == 'nt':
            subprocess.Popen(["explorer", path])
        else:
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', path])
        return f"✅ ফোল্ডার ওপেন হয়েছে: {path}"
    except Exception as e:
        return f"❌ ফোল্ডার খোলা যায়নি: {e}"


async def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ ফোল্ডার তৈরি হয়েছে: {path}"
    except Exception as e:
        return f"❌ ফোল্ডার তৈরি করা যায়নি: {e}"


async def rename_item(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"✅ নাম পরিবর্তন হয়েছে: {new_path}"
    except Exception as e:
        return f"❌ নাম পরিবর্তন ব্যর্থ: {e}"


async def delete_item(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        return f"✅ ডিলিট হয়েছে: {path}"
    except Exception as e:
        return f"❌ ডিলিট করা যায়নি: {e}"


async def play_file(path):
    return await open_file({"name": os.path.basename(path), "path": path, "type": "file"})


async def handle_command(command, index):
    item = await search_file(command, index)
    if item:
        return await open_file(item)
    else:
        logger.warning("❌ ফাইল পাওয়া যায়নি।")
        return "❌ ফাইল পাওয়া যায়নি।"


@function_tool
async def folder_file(command: str) -> str:
    folders_to_index = [
        "C:/Users/Farid-Myolbd/Desktop",
        "C:/Users/Farid-Myolbd/Documents",
        "C:/Users/Farid-Myolbd/Downloads",
        "C:/", "D:/", "E:/"
    ]
    index = await index_files(folders_to_index)
    command_lower = command.lower()

    if "create folder" in command_lower:
        folder_name = command.replace("create folder", "").strip()
        path = os.path.join("D:/", folder_name)
        return await create_folder(path)

    if "rename" in command_lower:
        parts = command_lower.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            item = await search_item(old_name, index, "folder")
            if item:
                new_path = os.path.join(os.path.dirname(item["path"]), new_name)
                return await rename_item(item["path"], new_path)
        return "❌ rename command valid নয়।"

    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "❌ delete করার মতো item পাওয়া যায়নি।"

    if any(word in command_lower for word in ["open", "folder", "search", "find", "look for"]):
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            if item["type"] == "folder":
                return await open_folder(item["path"])
            else:
                return await play_file(item["path"])
        return "❌ ফাইল বা ফোল্ডার খুঁজে পাওয়া যায়নি।"

    logger.warning(f"⚠ অজানা কমান্ড: {command}")
    return "⚠ আমি নিশ্চিত না আপনি কী করতে চাইছেন। দয়া করে কমান্ডটি স্পষ্টভাবে দিন।"
