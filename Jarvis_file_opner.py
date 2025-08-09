# jarvis_file_opner.py (Full PC Access Version - Bangla messages only)
import os
import shutil
import subprocess
import sys
import logging
import string
import asyncio
from functools import lru_cache
from fuzzywuzzy import process
from livekit.agents import function_tool

try:
    import pygetwindow as gw
except ImportError:
    gw = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# -------- CONFIG --------
def _list_drives():
    if os.name == "nt":
        return [f"{d}:/" for d in string.ascii_uppercase if os.path.exists(f"{d}:/")]
    return ["/"]

SEARCH_FOLDERS = _list_drives()

# -------- INDEX --------
@lru_cache(maxsize=1)
def _build_index():
    items = []
    for root in SEARCH_FOLDERS:
        for base, dirs, files in os.walk(root, onerror=lambda e: None):
            for f in files:
                items.append((f, os.path.join(base, f), "file"))
            for d in dirs:
                items.append((d, os.path.join(base, d), "folder"))
    logger.info("✅ মোট %dটি আইটেম ইনডেক্স করা হয়েছে।", len(items))
    return items

def _search_one(name: str, kind: str | None = None):
    idx = _build_index()
    pool = [(n, p, t) for n, p, t in idx if kind is None or t == kind]
    if not pool:
        return None
    match, score = process.extractOne(name, [n for n, _, _ in pool]) or (None, 0)
    return next((n, p, t) for n, p, t in pool if n == match) if score > 70 else None

def _open_native(path: str):
    if os.name == "nt":
        subprocess.Popen(["cmd", "/c", "start", "", f'"{path}"'], shell=False)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

async def _focus(title_keyword: str) -> bool:
    if not gw:
        return False
    await asyncio.sleep(0.5)
    kw = title_keyword.lower()
    for w in gw.getAllWindows():
        if kw in w.title.lower():
            if w.isMinimized:
                w.restore()
            w.activate()
            return True
    return False

# -------- TOOLS --------
@function_tool
async def Play_file(name: str) -> str:
    """ফাইল খোঁজা ও খোলা"""
    hit = _search_one(name.strip(), "file")
    if not hit:
        return "❌ ফাইল পাওয়া যায়নি।"
    _, path, _ = hit
    _open_native(path)
    await _focus(os.path.basename(path))
    return f"✅ ফাইল খোলা হয়েছে: {os.path.basename(path)}"

@function_tool
async def folder_file(command: str) -> str:
    """ফোল্ডার/ফাইল পরিচালনার কমান্ড"""
    cmd = command.strip().lower()

    # Create folder
    if cmd.startswith("create folder"):
        folder_name = command[13:].strip()
        if not folder_name:
            return "❌ ফোল্ডারের নাম দিন।"
        new_path = os.path.join("D:/", folder_name)
        os.makedirs(new_path, exist_ok=True)
        return f"✅ ফোল্ডার তৈরি হয়েছে: {new_path}"

    # Create file
    if cmd.startswith("create file"):
        file_name = command[11:].strip()
        if not file_name:
            return "❌ ফাইলের নাম দিন।"
        new_path = os.path.join("D:/", file_name)
        open(new_path, "w", encoding="utf-8").close()
        return f"✅ ফাইল তৈরি হয়েছে: {new_path}"

    # Read file
    if cmd.startswith("read file"):
        file_name = command[9:].strip()
        hit = _search_one(file_name, "file")
        if not hit:
            return "❌ ফাইল পাওয়া যায়নি।"
        _, path, _ = hit
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"❌ ফাইল পড়া যায়নি: {e}"

    # Write file
    if cmd.startswith("write file"):
        parts = command[10:].split("::", 1)
        if len(parts) != 2:
            return "❌ ফরম্যাট: write file filename :: content"
        file_name, content = parts
        hit = _search_one(file_name.strip(), "file")
        if not hit:
            return "❌ ফাইল পাওয়া যায়নি।"
        _, path, _ = hit
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ ফাইল আপডেট হয়েছে: {path}"
        except Exception as e:
            return f"❌ ফাইল লেখা যায়নি: {e}"

    # Rename
    if "rename" in cmd and " to " in cmd:
        old, new = cmd.replace("rename", "").split(" to ", 1)
        hit = _search_one(old.strip())
        if not hit:
            return "❌ মূল আইটেম খুঁজে পাওয়া যায়নি।"
        _, old_path, _ = hit
        new_path = os.path.join(os.path.dirname(old_path), new.strip())
        os.rename(old_path, new_path)
        return f"✅ নাম পরিবর্তন: {old_path} → {new_path}"

    # Delete
    if cmd.startswith("delete"):
        name = command[6:].strip()
        hit = _search_one(name)
        if not hit:
            return "❌ আইটেম খুঁজে পাওয়া যায়নি।"
        _, path, typ = hit
        if typ == "file":
            os.remove(path)
        else:
            shutil.rmtree(path)
        return f"✅ ডিলিট হয়েছে: {path}"

    # Move
    if cmd.startswith("move"):
        parts = command[4:].split(" to ", 1)
        if len(parts) != 2:
            return "❌ ফরম্যাট: move source to destination"
        src_name, dest_folder = parts
        hit = _search_one(src_name.strip())
        if not hit:
            return "❌ সোর্স খুঁজে পাওয়া যায়নি।"
        _, src_path, _ = hit
        shutil.move(src_path, dest_folder.strip())
        return f"✅ মুভ হয়েছে: {src_path} → {dest_folder}"

    # Copy
    if cmd.startswith("copy"):
        parts = command[4:].split(" to ", 1)
        if len(parts) != 2:
            return "❌ ফরম্যাট: copy source to destination"
        src_name, dest_folder = parts
        hit = _search_one(src_name.strip())
        if not hit:
            return "❌ সোর্স খুঁজে পাওয়া যায়নি।"
        _, src_path, typ = hit
        if typ == "file":
            shutil.copy2(src_path, dest_folder.strip())
        else:
            shutil.copytree(src_path, os.path.join(dest_folder.strip(), os.path.basename(src_path)))
        return f"✅ কপি হয়েছে: {src_path} → {dest_folder}"

    # Shutdown
    if cmd == "shutdown":
        os.system("shutdown /s /t 1")
        return "💤 সিস্টেম শাটডাউন হচ্ছে..."

    # Restart
    if cmd == "restart":
        os.system("shutdown /r /t 1")
        return "🔄 সিস্টেম রিস্টার্ট হচ্ছে..."

    # Log off
    if cmd == "log off":
        os.system("shutdown /l")
        return "🚪 সিস্টেম লগ অফ হচ্ছে..."

    # Open
    hit = _search_one(command)
    if not hit:
        return "❌ আইটেম খুঁজে পাওয়া যায়নি।"
    _, path, typ = hit
    _open_native(path)
    await _focus(os.path.basename(path))
    return f"✅ খোলা হয়েছে ({typ}): {os.path.basename(path)}"
