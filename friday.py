import speech_recognition as sr
import pyttsx3
import wikipedia
import time
import os  # For PC interactions
import random

# Initialize TTS
engine = pyttsx3.init()
engine.setProperty('rate', 175)
engine.setProperty('voice', engine.getProperty('voices')[1].id)

def speak(text):
    print(f"\n🗣️ FRIDAY: {text}\n")
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Listening... Speak clearly.")
        audio = recognizer.listen(source, phrase_time_limit=7)
    try:
        query = recognizer.recognize_google(audio).lower()
        print(f"✅ You said: {query}")
        return query
    except sr.UnknownValueError:
        speak("❌ Sorry, I didn't understand.")
        return None
    except sr.RequestError:
        speak("❌ Network error. Try again.")
        return None

def extract_topic(command):
    keywords = ["tell me about", "who is", "what is", "search for", "define"]
    for key in keywords:
        if key in command:
            return command.split(key)[-1].strip()
    return command

def search_wikipedia(topic):
    try:
        summary = wikipedia.summary(topic, sentences=3)
        speak(f"🔍 Here's what I found about {topic}:")
        speak(summary)
        print(f"🔗 Source: https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}")
    except wikipedia.DisambiguationError:
        speak("Too many results. Can you be more specific?")
    except wikipedia.PageError:
        speak("I couldn't find anything about that.")
    except Exception as e:
        print("Error:", e)
        speak("Something went wrong.")

def ask_you_something():
    questions = [
        "How are you today?",
        "Do you want to hear the latest news?",
        "Shall I tell you a fun fact?",
        "Do you want to open any application?"
    ]
    q = random.choice(questions)
    speak(q)
    response = listen()
    return response

def open_app(app_name):
    try:
        if "notepad" in app_name:
            os.system("start notepad")
            speak("📝 Opening Notepad.")
        elif "chrome" in app_name:
            os.system("start chrome")
            speak("🌐 Opening Chrome.")
        else:
            speak("I don't know that app yet.")
    except:
        speak("Sorry, I couldn't open that.")

def friday():
    speak("Hello, I am FRIDAY, your assistant.")
    time.sleep(1)

    while True:
        # Proactive question first
        user_reply = ask_you_something()
        if user_reply:
            if "yes" in user_reply:
                speak("Alright, go ahead!")
            elif "no" in user_reply:
                speak("Okay, let's do something else.")

        command = listen()
        if not command:
            continue
        if "exit" in command or "stop" in command:
            speak("👋 Goodbye, see you later!")
            break

        elif "open" in command:
            open_app(command)

        else:
            topic = extract_topic(command)
            if topic:
                speak(f"Searching Wikipedia for {topic}...")
                search_wikipedia(topic)
            else:
                speak("Please tell me what to search for.")

# Start
if __name__ == "__main__":
    friday()
