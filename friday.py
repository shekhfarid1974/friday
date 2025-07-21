import speech_recognition as sr
import pyttsx3
from googlesearch import search
import time

engine = pyttsx3.init()
engine.setProperty('rate', 140)
engine.setProperty('volume', 1.0)

def speak(text):
    print("FRIDAY:", text)
    engine.say(text)
    engine.runAndWait()

def listen_command():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.0  # wait longer before assuming user stopped speaking
    with sr.Microphone() as source:
        print("\n🎙️ Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        print("Energy threshold:", recognizer.energy_threshold)
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio, language='en-US')
        print("You said:", command)
        return command.lower()
    except sr.UnknownValueError:
        print("Sorry, I did not catch that.")
        return None
    except sr.RequestError:
        print("Speech recognition failed.")
        return None

def google_search(query, num_results=5):
    print(f"Searching Google for: {query}")
    urls = []
    try:
        for url in search(query, num_results=num_results, lang="en"):
            print(url)
            urls.append(url)
    except Exception as e:
        print("Search error:", e)
    return urls

def main():
    speak("Hi, I am FRIDAY. You can ask me to search anything.")
    while True:
        command = listen_command()
        if command:
            if any(exit_word in command for exit_word in ["exit", "stop", "bye", "quit"]):
                speak("Goodbye! Have a nice day.")
                break

            if "search" in command or "google" in command:
                # Extract search query by removing "search" or "google"
                query = command.replace("search", "").replace("google", "").strip()
                if not query:
                    speak("Please tell me what to search for.")
                    continue
                speak(f"Searching Google for {query}")
                google_search(query)
            else:
                speak("I can search the internet for you. Just say 'search' or 'google' followed by your query.")
        else:
            speak("Please say that again.")
        time.sleep(1)

if __name__ == "__main__":
    main()
