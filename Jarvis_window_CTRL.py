import os
import subprocess
import logging
import sys
import asyncio
from fuzzywuzzy import process

try:
    from livekit.agents import function_tool
except ImportError:
    def function_tool(func): 
        return func

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

# Setup encoding and logger
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App command map
APP_MAPPINGS = {
    "notepad": "notepad",
    "calculator": "calc",
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
    "command prompt": "cmd",
    "control panel": "control",
    "settings": "start ms-settings:",
    "paint": "mspaint",
    "vs code": "C:\\Users\\gaura\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
    "postman": "C:\\Users\\gaura\\AppData\\Local\\Postman\\Postman.exe"
}

# -------------------------
# Global focus utility
# -------------------------
async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow পাওয়া যায়নি")
        return False

    await asyncio.sleep(1.5)
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
    return False

# Index files/folders
async def index_items(base_dirs):
    item_index = []
    for base_dir in base_dirs:
        for root, dirs, files in os.walk(base_dir):
            for d in dirs:
                item_index.append({"name": d, "path": os.path.join(root, d), "type": "folder"})
            for f in files:
                item_index.append({"name": f, "path": os.path.join(root, f), "type": "file"})
    logger.info(f"✅ {len(item_index)} টি ফাইল ও ফোল্ডার সূচিভুক্ত হয়েছে।")
    return item_index

async def search_item(query, index, item_type):
    filtered = [item for item in index if item["type"] == item_type]
    choices = [item["name"] for item in filtered]
    if not choices:
        return None
    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 '{query}' এর জন্য মিলেছে '{best_match}' স্কোর {score}")
    if score > 70:
        for item in filtered:
            if item["name"] == best_match:
                return item
    return None

# File/folder actions
async def open_folder(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ ফোল্ডার খোলার সময় সমস্যা হয়েছে: {e}")

async def play_file(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ ফাইল চালু করতে ব্যর্থ: {e}")

async def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ ফোল্ডার তৈরি হয়েছে: {path}"
    except Exception as e:
        return f"❌ ফোল্ডার তৈরি করতে সমস্যা হয়েছে: {e}"

async def rename_item(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"✅ নাম পরিবর্তন করা হয়েছে: {new_path}"
    except Exception as e:
        return f"❌ নাম পরিবর্তন করতে ব্যর্থ: {e}"

async def delete_item(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"🗑️ মুছে ফেলা হয়েছে: {path}"
    except Exception as e:
        return f"❌ মুছে ফেলা যায়নি: {e}"

# App control
@function_tool
async def open(app_title: str) -> str:
    app_title = app_title.lower().strip()
    app_command = APP_MAPPINGS.get(app_title, app_title)
    try:
        await asyncio.create_subprocess_shell(f'start "" "{app_command}"', shell=True)
        focused = await focus_window(app_title)
        if focused:
            return f"🚀 অ্যাপ চালু হয়েছে এবং ফোকাসে আছে: {app_title}."
        else:
            return f"🚀 {app_title} চালু হয়েছে, কিন্তু উইন্ডোতে ফোকাস হয়নি।"
    except Exception as e:
        return f"❌ {app_title} চালু করা যায়নি: {e}"

@function_tool
async def close(window_title: str) -> str:
    if not win32gui:
        return "❌ win32gui পাওয়া যায়নি"

    def enumHandler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            if window_title.lower() in win32gui.GetWindowText(hwnd).lower():
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

    win32gui.EnumWindows(enumHandler, None)
    return f"❌ উইন্ডো বন্ধ করা হয়েছে: {window_title}"

# Jarvis command logic
@function_tool
async def folder_file(command: str) -> str:
    folders_to_index = ["D:/"]
    index = await index_items(folders_to_index)
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
        return "❌ রিনেম কমান্ড সঠিক নয়।"

    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "❌ মুছে ফেলার জন্য আইটেম পাওয়া যায়নি।"

    if "folder" in command_lower or "open folder" in command_lower:
        item = await search_item(command, index, "folder")
        if item:
            await open_folder(item["path"])
            return f"✅ ফোল্ডার খোলা হয়েছে: {item['name']}"
        return "❌ ফোল্ডার পাওয়া যায়নি।"

    item = await search_item(command, index, "file")
    if item:
        await play_file(item["path"])
        return f"✅ ফাইল খোলা হয়েছে: {item['name']}"

    return "⚠ কোন মেলা পাওয়া যায়নি।"
