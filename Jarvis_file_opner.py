# jarvis_file_opner.py  (Bangla messages only)
import os
import shutil
import subprocess
import sys
import logging
from functools import lru_cache
from fuzzywuzzy import process
from livekit.agents import function_tool
import asyncio

try:
    import pygetwindow as gw
except ImportError:
    gw = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------- CONFIG ----------
# সম্ভাব্য সব ড্রাইভ অটো-ডিটেক্ট করে নেওয়া
import string


def _list_drives():
    if os.name == "nt":
        return [f"{d}:/" for d in string.ascii_uppercase if os.path.exists(f"{d}:/")]
    return ["/"]


SEARCH_FOLDERS = _list_drives()


# ---------- CACHED INDEX ----------
@lru_cache(maxsize=1)
def _build_index():
    """একবার ইনডেক্স তৈরি করে ক্যাশে রাখে।"""
    items = []
    for root in SEARCH_FOLDERS:
        for base, _, files in os.walk(root, onerror=lambda e: None):
            for f in files:
                items.append((f, os.path.join(base, f), "file"))
            for d in _:
                items.append((d, os.path.join(base, d), "folder"))
    logger.info("✅ মোট %dটি আইটেম ইনডেক্স করা হয়েছে।", len(items))
    return items


def _search_one(name: str, kind: str | None = None):
    """নাম অনুযায়ী সবচেয়ে কাছের আইটেম খুঁজে দেয়।"""
    idx = _build_index()
    pool = [(n, p, t) for n, p, t in idx if kind is None or t == kind]
    if not pool:
        return None
    match, score = process.extractOne(name, [n for n, _, _ in pool]) or (None, 0)
    return next((n, p, t) for n, p, t in pool if n == match) if score > 70 else None


def _open_native(path: str):
    """সিস্টেম ডিফল্ট অ্যাপ্লিকেশন দিয়ে ফাইল/ফোল্ডার খোলে।"""
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


# ---------- TOOLS ----------
@function_tool
async def Play_file(name: str) -> str:
    hit = _search_one(name.strip(), "file")
    if not hit:
        return "❌ ফাইল পাওয়া যায়নি।"
    _, path, _ = hit
    _open_native(path)
    await _focus(os.path.basename(path))
    return f"✅ ফাইল খোলা হয়েছে: {os.path.basename(path)}"


@function_tool
async def folder_file(command: str) -> str:
    command = command.strip()
    cmd_lower = command.lower()

    if cmd_lower.startswith("create folder"):
        folder_name = command[13:].strip()
        if not folder_name:
            return "❌ ফোল্ডারের নাম দিন।"
        new_path = os.path.join("D:/", folder_name)
        os.makedirs(new_path, exist_ok=True)
        return f"✅ ফোল্ডার তৈরি হয়েছে: {new_path}"

    if "rename" in cmd_lower and " to " in cmd_lower:
        old, new = cmd_lower.replace("rename", "").split(" to ", 1)
        hit = _search_one(old.strip())
        if not hit:
            return "❌ মূল আইটেম খুঁজে পাওয়া যায়নি।"
        _, old_path, _ = hit
        new_path = os.path.join(os.path.dirname(old_path), new.strip())
        os.rename(old_path, new_path)
        return f"✅ নাম পরিবর্তন: {old_path} → {new_path}"

    if cmd_lower.startswith("delete"):
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

    hit = _search_one(command)
    if not hit:
        return "❌ আইটেম খুঁজে পাওয়া যায়নি।"
    _, path, typ = hit
    _open_native(path)
    await _focus(os.path.basename(path))
    return f"✅ খোলা হয়েছে ({typ}): {os.path.basename(path)}"
