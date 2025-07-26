# friday.py (Updated)
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import os
import pyautogui
import json
import openai
import pvporcupine
import pyaudio
import struct
import threading
import queue
from dotenv import load_dotenv
# Import the speak function and TTS worker from utils
# Remove the old TTS code from here
from utils import speak, stop_tts # speak_worker, speak_queue, engine_lock are internal to utils now
# Import the brain function
from brain import search_google_and_respond
from bs4 import BeautifulSoup # Might be used by brain or other parts, keep if needed
import requests # Might be used by brain or other parts, keep if needed

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
porcupine_access_key = os.getenv("PORCUPINE_ACCESS_KEY")

if not porcupine_access_key:
    print("❌ PORCUPINE_ACCESS_KEY not found in .env file.")
    exit()

# ----------------------------- (REMOVE THE OLD TTS CODE FROM HERE) -----------------------------
# All the TTS code (speak_queue, engine_lock, speak_worker, speak function) has been moved to utils.py
# Do not duplicate it here.
# ---------------------------------------------------------------------------------------

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

    # --- Handle specific commands ---
    if 'wikipedia' in query:
        speak("🔍 Searching Wikipedia...")
        try:
            # Improve query extraction
            search_term = query.replace("wikipedia", "").strip()
            if search_term:
                result = wikipedia.summary(search_term, sentences=2)
                speak("According to Wikipedia: " + result)
            else:
                 speak("What would you like to search on Wikipedia?")
        except Exception as e: # Catch specific exceptions if possible
            print(f"Wikipedia error: {e}") # Log the error
            speak("No results found on Wikipedia or an error occurred.")

    elif 'open youtube' in query:
        webbrowser.open("https://youtube.com")
        speak("🚀 Opening YouTube.")

    elif 'open google' in query:
        webbrowser.open("https://google.com")
        speak("🌐 Opening Google.")

    elif 'time' in query:
        time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {time}.")

    elif 'date' in query:
        date = datetime.date.today().strftime("%B %d, %Y")
        speak(f"Today is {date}.")

    elif 'search for' in query and 'on google' in query:
        # --- Use the new brain function ---
        term = query.replace("search for", "").replace("on google", "").strip()
        # Instead of just opening the browser, get the info
        # webbrowser.open(f"https://google.com/search?q={term}")
        # speak(f"🔎 Searching Google for {term}.")
        search_google_and_respond(term) # This handles speaking/printing

    elif 'take screenshot' in query:
        try: # Add error handling
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            pyautogui.screenshot(filename)
            speak("📸 Screenshot saved.")
        except Exception as e:
             print(f"Screenshot error: {e}")
             speak("Failed to take screenshot.")

    elif 'remember that' in query:
        try:
            key_value = query.replace("remember that", "").strip()
            if "=" in key_value:
                key, value = map(str.strip, key_value.split("=", 1))
            else:
                key, value = "note", key_value
            memory[key] = value
            save_memory(memory)
            speak(f"✅ Remembered: {key}.")
        except Exception as e:
             print(f"Memory error: {e}")
             speak("Failed to remember that.")

    elif 'what did i say about' in query:
        try:
            key = query.replace("what did i say about", "").strip()
            value = memory.get(key, "No record found.")
            speak(value)
        except Exception as e:
             print(f"Memory retrieval error: {e}")
             speak("Failed to retrieve that information.")

    elif 'bye' in query or 'sleep' in query:
        speak("💤 Going to standby mode.")
        start_wake_word_detection()
        return

    # --- Handle general queries by asking the brain first ---
    # Check for common question starters
    elif any(keyword in query for keyword in ['tell me about', 'what is', 'who is', 'how do', 'why is', 'define']):
         # Extract the core question part (basic example)
         # You might want a more sophisticated way to extract the search term
         search_term = query
         # Simple removal of common prefixes
         prefixes = ['hey friday', 'friday', 'tell me about', 'what is', 'who is', 'how do', 'why is', 'define']
         for prefix in prefixes:
             # Use lower() for case-insensitive matching
             if search_term.startswith(prefix.lower()):
                  search_term = search_term[len(prefix):].strip()
                  break
         # Remove trailing punctuation if needed
         search_term = search_term.rstrip('?.,!')
         if search_term:
             search_google_and_respond(search_term)
         else:
              # Fallback to GPT if brain can't handle or query is unclear
              speak("💭 Thinking...")
              reply = gpt_query(query)
              speak(reply)
    else:
        # Default to GPT for other commands
        speak("💭 Thinking...")
        reply = gpt_query(query)
        speak(reply)

    # After any command, return to wake-word mode after a short delay
    # Consider if this is always desired, or only for specific cases
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
            # Ensure the .ppn file path is correct relative to where you run the script
            porcupine = pvporcupine.create(
                access_key=porcupine_access_key,
                keyword_paths=["hey-friday_en_windows_v3_0_0.ppn"]  # ← Make sure this file exists in the correct path!
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
                        break # Exit the loop and trigger command mode
                except Exception as e:
                    print("👂 Audio read error:", e)
                    break # Exit on audio error

        except Exception as e:
            speak("⚠️ Failed to start wake word detection.")
            print("❌ Porcupine Error:", e)
        finally:
            # Cleanup resources
            wake_word_active = False # Reset flag BEFORE cleanup
            if stream:
                stream.close()
            if pa:
                pa.terminate()
            if porcupine:
                porcupine.delete()

        # Switch to command mode AFTER cleanup
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
        # Signal the TTS thread to stop via utils
        stop_tts()
        # Give it a moment to finish (optional, but good practice)
        # from utils import tts_thread
        # tts_thread.join(timeout=2)
        os._exit(0) # Force exit cleanly
