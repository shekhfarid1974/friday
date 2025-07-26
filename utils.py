# utils.py
import pyttsx3
import threading
import queue

# -----------------------------
# Thread-Safe Text-to-Speech System
# -----------------------------
speak_queue = queue.Queue()
engine_lock = threading.Lock()

def speak_worker():
    """Background worker for speaking (runs in one thread only)"""
    engine = pyttsx3.init('sapi5') # Adjust for your OS if needed (e.g., 'nsss' for Mac)
    voices = engine.getProperty('voices')
    # Try to find a female voice, fallback to default [0]
    # You might need to adjust the index based on your system's voices
    female_voice_index = None
    for i, voice in enumerate(voices):
         # Common identifiers for female voices, adjust as needed
         if 'female' in voice.name.lower() or 'zira' in voice.name.lower(): # Example for Windows
             female_voice_index = i
             break
    if female_voice_index is not None:
        engine.setProperty('voice', voices[female_voice_index].id)
    else:
         print("Female voice not found, using default.")
         engine.setProperty('voice', voices[0].id) # Fallback to first voice

    print(f"Available TTS Voices:")
    for i, voice in enumerate(voices):
        print(f"  [{i}] {voice.name} - {voice.id}")

    while True:
        text = speak_queue.get()
        if text is None:
            break
        with engine_lock:
            try:
                print(f"F.R.I.D.A.Y.: {text}") # Print before speaking
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
    # Print handled inside worker now, but you could also print here if preferred
    # print(f"F.R.I.D.A.Y.: {text}")
    speak_queue.put(text)

# Optional: Function to stop the TTS thread cleanly
def stop_tts():
    speak_queue.put(None)
    # Optionally join if you need to wait for it to finish
    # tts_thread.join()
