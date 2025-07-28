# friday.py (Updated - PyAudio import removed)
# NOTE: This assumes take_command uses text input and wake word detection
# no longer relies on PyAudio or the old start_wake_word_detection logic.

import datetime
import wikipedia
import webbrowser
import os
import pyautogui
import json
import openai
# import pvporcupine # Remove/comment if wake word logic is also changed
# import pyaudio      # *** REMOVED PYAUDIO IMPORT ***
# import struct       # Remove if not used elsewhere and wake word is changed
import threading
import queue
from dotenv import load_dotenv
# Import the speak function and TTS worker from utils
from utils import speak, stop_tts # speak_worker, speak_queue, engine_lock are internal to utils now
# Import the brain function
from brain import search_google_and_respond
from bs4 import BeautifulSoup # Keep if used by brain.py or other parts
import requests # Keep if used by brain.py or other parts

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
# porcupine_access_key = os.getenv("PORCUPINE_ACCESS_KEY") # Remove/comment if not used
# if not porcupine_access_key: # Remove/comment if not used
#     print("❌ PORCUPINE_ACCESS_KEY not found in .env file.")
#     exit() # Remove/comment if not used


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
# Text Command Handler (Modified as discussed)
# -----------------------------
def take_command():
    """
    Gets command via text input instead of voice.
    This removes the dependency on PyAudio.
    """
    try:
        print("\n--- F.R.I.D.A.Y. Text Input Mode ---")
        print("Type your command and press Enter.")
        print("Examples: 'search for the weather on google', 'tell me about AI', 'time', 'open youtube'")
        print("Type 'exit' or 'quit' to stop F.R.I.D.A.Y.")
        print("-------------------------------------")
        user_input = input("🗣️ >>> ")
        user_input = user_input.strip() # Remove leading/trailing whitespace

        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("🛑 Exiting F.R.I.D.A.Y. Text Mode.")
            return "exit_friday" # Special command to trigger shutdown

        if not user_input: # Handle empty input
             print("⚠️ No input received.")
             return "none"

        print(f"👤 User said (via text): {user_input}")
        return user_input.lower()
    except KeyboardInterrupt:
        print("\n\n🛑 Received Ctrl+C interrupt.")
        return "exit_friday" # Treat Ctrl+C as exit command
    except Exception as e:
        print(f"❌ Error getting text input: {e}")
        speak("Sorry, there was an error getting your text input.")
        return "none"


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
        # start_wake_word_detection() # Remove/comment if wake word is gone
        # For text mode, maybe just loop back or exit?
        return # Just return, let command_mode_loop handle the loop

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

    # Removed the timer that calls start_wake_word_detection for text mode


# -----------------------------
# Command Mode (Updated for Text Exit)
# -----------------------------
def command_mode():
    """ Single command execution """
    query = take_command()
    if query == "exit_friday":
        # Trigger shutdown
        print("🛑 F.R.I.D.A.Y. shutting down...")
        speak("👋 Goodbye, sir. F.R.I.D.A.Y. signing off.")
        # Schedule TTS stop and exit
        threading.Timer(1.0, lambda: (stop_tts(), os._exit(0))).start()
        return # Exit command_mode
    elif query != "none":
        process_command(query)
    else:
        # Optional: Handle 'none' case (e.g., error or empty input)
        # For text mode, you might just loop back
        pass
    # In text mode, you might want to call command_mode again immediately
    # instead of waiting for wake word.
    # However, if you want to mimic wake-word behavior, leave the timer.
    # For continuous text input, see command_mode_loop below.

# -----------------------------
# Wake Word Detection (REMOVED/COMMENTED OUT)
# -----------------------------
# The original start_wake_word_detection function which used pyaudio and pvporcupine
# has been removed or commented out as it requires PyAudio.
# If you have a new implementation using sounddevice, it would go here.
# def start_wake_word_detection():
#     # ... new sounddevice-based logic ...
#     pass

# -----------------------------
# Startup & Main Loop (Updated for Text Mode)
# -----------------------------
def wish_me():
    hour = datetime.datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    speak(f"{greeting}, sir. I am F.R.I.D.A.Y. Ready when you are.")

def command_mode_loop():
    """Runs the command mode in a continuous loop for text input."""
    print("🎧 F.R.I.D.A.Y. initialized in text mode. Awaiting commands.")
    while True:
        query = take_command()
        if query == "exit_friday":
            print("🛑 F.R.I.D.A.Y. shutting down...")
            speak("👋 Goodbye, sir. F.R.I.D.A.Y. signing off.")
            # Schedule TTS stop and exit to allow speech to finish
            threading.Timer(1.5, lambda: (stop_tts(), os._exit(0))).start()
            break # Exit the loop
        elif query != "none":
            process_command(query)
        # Add a small pause if needed, though input() is blocking
        # time.sleep(0.1)

if __name__ == "__main__":
    try:
        wish_me()
        # Instead of wake word, start the command loop directly
        command_mode_loop() # Use the continuous text input loop

        # Original loop removed for text mode:
        # start_wake_word_detection()
        # Keep main thread alive
        # while True:
        #     threading.Event().wait(1)  # Sleep 1 sec, wait for interrupt

    except Exception as e: # Catch unexpected errors in main thread
         print(f"❌ Unexpected error in main loop: {e}")
         speak("An unexpected error occurred. Shutting down.")
         stop_tts()
         os._exit(1)
