import pyttsx3
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import os
import pyautogui
import requests
import json
import openai
import pvporcupine
import pyaudio
import struct
import threading
import queue
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
porcupine_access_key = os.getenv("PORCUPINE_ACCESS_KEY")

if not porcupine_access_key:
    print("❌ PORCUPINE_ACCESS_KEY not found in .env file.")
    exit()

# -----------------------------
# Thread-Safe Text-to-Speech System
# -----------------------------
speak_queue = queue.Queue()
engine_lock = threading.Lock()

def speak_worker():
    """Background worker for speaking (runs in one thread only)"""
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # Female voice (change to [0] for male)

    while True:
        text = speak_queue.get()
        if text is None:
            break
        with engine_lock:
            try:
                engine.say(text)
                engine.runAndWait()
            except RuntimeError as e:
                if "run loop already started" in str(e):
                    print("⚠️ TTS engine busy, skipping...")
                else:
                    print("❌ TTS Error:", e)
    engine.stop()

# Start TTS worker thread
tts_thread = threading.Thread(target=speak_worker, daemon=True)
tts_thread.start()

def speak(text):
    """Thread-safe speak function"""
    print(f"F.R.I.D.A.Y.: {text}")
    speak_queue.put(text)

# -----------------------------
# Memory System
# -----------------------------
def load_memory():
    if not os.path.exists("memory.json"):
        return {}
    try:
        with open("memory.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print("⚠️ Memory load failed:", e)
        return {}

def save_memory(data):
    try:
        with open("memory.json", "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("⚠️ Could not save memory:", e)

memory = load_memory()

# -----------------------------
# GPT Query Function
# -----------------------------
def gpt_query(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are F.R.I.D.A.Y., Tony Stark's intelligent AI assistant. Be concise, witty, and professional."},
                {"role": "user", "content": prompt}
            ],
            timeout=10
        )
        return response.choices[0].message['content']
    except Exception as e:
        return "I'm having trouble connecting to the AI service right now."

# -----------------------------
# Voice Command Handler
# -----------------------------
def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Listening for command...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        except:
            return "None"
    try:
        query = r.recognize_google(audio, language='en-in').lower()
        print(f"👤 User said: {query}")
        return query
    except:
        speak("Sorry, I didn't catch that.")
        return "None"

# -----------------------------
# Command Processor
# -----------------------------
def process_command(query):
    global memory
    print(f"🧠 Processing: {query}")

    if 'wikipedia' in query:
        speak("🔍 Searching Wikipedia...")
        try:
            result = wikipedia.summary(query.replace("wikipedia", "").strip(), sentences=2)
            speak("According to Wikipedia: " + result)
        except:
            speak("No results found on Wikipedia.")
    
    elif 'open youtube' in query:
        webbrowser.open("https://youtube.com ")
        speak("🚀 Opening YouTube.")

    elif 'open google' in query:
        webbrowser.open("https://google.com ")
        speak("🌐 Opening Google.")

    elif 'time' in query:
        time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {time}.")

    elif 'date' in query:
        date = datetime.date.today().strftime("%B %d, %Y")
        speak(f"Today is {date}.")

    elif 'search for' in query and 'on google' in query:
        term = query.replace("search for", "").replace("on google", "").strip()
        webbrowser.open(f"https://google.com/search?q={term}")
        speak(f"🔎 Searching Google for {term}.")

    elif 'take screenshot' in query:
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pyautogui.screenshot(filename)
        speak("📸 Screenshot saved.")

    elif 'remember that' in query:
        key_value = query.replace("remember that", "").strip()
        if "=" in key_value:
            key, value = map(str.strip, key_value.split("=", 1))
        else:
            key, value = "note", key_value
        memory[key] = value
        save_memory(memory)
        speak(f"✅ Remembered: {key}.")

    elif 'what did i say about' in query:
        key = query.replace("what did i say about", "").strip()
        value = memory.get(key, "No record found.")
        speak(value)

    elif 'bye' in query or 'sleep' in query:
        speak("💤 Going to standby mode.")
        start_wake_word_detection()
        return

    else:
        speak("💭 Thinking...")
        reply = gpt_query(query)
        speak(reply)

    # After any command, return to wake-word mode after a short delay
    threading.Timer(2.0, start_wake_word_detection).start()

# -----------------------------
# Command Mode (After Wake Word)
# -----------------------------
def command_mode():
    query = take_command()
    if query != "None":
        process_command(query)
    else:
        speak("I didn't hear anything.")
        start_wake_word_detection()  # Return anyway

# -----------------------------
# Wake Word Detection (Single Instance Only)
# -----------------------------
wake_word_active = False

def start_wake_word_detection():
    global wake_word_active

    if wake_word_active:
        return  # Prevent duplicate listeners
    wake_word_active = True

    def detect():
        global wake_word_active
        porcupine = None
        pa = None
        stream = None

        try:
            # Initialize Porcupine
            porcupine = pvporcupine.create(
                access_key=porcupine_access_key,
                keyword_paths=["hey-friday_en_windows_v3_0_0.ppn"]  # ← Make sure this file exists!
            )

            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )

            speak("🎧 F.R.I.D.A.Y. is now on standby...")
            print("🔊 Listening for 'Hey Friday...' (Press Ctrl+C to quit)")

            while wake_word_active:
                try:
                    pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                    pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)
                    if porcupine.process(pcm_unpacked) >= 0:
                        speak("👋 Yes, sir?")
                        break
                except Exception as e:
                    print("👂 Audio read error:", e)
                    break

        except Exception as e:
            speak("⚠️ Failed to start wake word detection.")
            print("❌ Porcupine Error:", e)
        finally:
            # Cleanup resources
            if stream:
                stream.close()
            if pa:
                pa.terminate()
            if porcupine:
                porcupine.delete()
            wake_word_active = False

        # Switch to command mode
        command_mode()

    # Run in background thread
    threading.Thread(target=detect, daemon=True).start()


# -----------------------------
# Startup & Main Loop
# -----------------------------
def wish_me():
    hour = datetime.datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    speak(f"{greeting}, sir. I am F.R.I.D.A.Y. Ready when you are.")

if __name__ == "__main__":
    try:
        wish_me()
        start_wake_word_detection()

        # Keep main thread alive
        while True:
            threading.Event().wait(1)  # Sleep 1 sec, wait for interrupt

    except KeyboardInterrupt:
        speak("👋 Goodbye, sir. F.R.I.D.A.Y. signing off.")
        speak_queue.put(None)  # Stop TTS thread
        os._exit(0)