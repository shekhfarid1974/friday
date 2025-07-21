import speech_recognition as sr
import wikipedia
import time
import pyttsx3

# Setup text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 175)

def speak(text):
    print(f"\n🗣️ FRIDAY: {text}")
    tts_engine.say(text)
    tts_engine.runAndWait()
    time.sleep(0.5)  # Short pause after speaking

def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎙️ Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            print("⏱️ Timeout waiting for speech.")
            return None

    try:
        command = recognizer.recognize_google(audio)
        print(f"✅ You said: {command}")
        return command.lower().strip()
    except sr.UnknownValueError:
        print("❌ Could not understand.")
        return None
    except sr.RequestError:
        print("❌ API unavailable.")
        return None

def extract_topic(command):
    keywords = ["tell me about", "can you tell me about", "search for", "search", "who is", "what is", "define", "know about"]
    for phrase in keywords:
        if phrase in command:
            return command.split(phrase)[-1].strip()
    return command  # fallback: assume entire command is the topic

def search_wikipedia(topic):
    try:
        speak(f"Searching Wikipedia for {topic}...")
        print(f"🗣️ FRIDAY: Searching for {topic}...")

        # Set language and search
        wikipedia.set_lang("en")
        page = wikipedia.page(topic)
        time.sleep(0.8)

        summary = wikipedia.summary(topic, sentences=2)
        speak(summary)
        print(f"\n🗣️ FRIDAY: {summary}\n")

        print(f"🔗 Source: {page.url}")
        speak("You can read more at the link I found.")
        speak("Want to know anything else?")

    except wikipedia.DisambiguationError as e:
        speak("That topic is a bit confusing. Please be more specific.")
        print("⚠️ Disambiguation error:", e.options)

    except wikipedia.PageError:
        speak("Sorry, I couldn't find any results for that.")
        print("❌ Wikipedia page not found.")

    except Exception as e:
        speak("Something went wrong while searching.")
        print(f"❌ Error: {str(e)}")

def main():
    speak("Hi, I am FRIDAY. You can ask me anything.")

    while True:
        command = listen_command()
        if not command:
            continue

        if "exit" in command or "stop" in command:
            speak("Goodbye. FRIDAY signing off.")
            break

        topic = extract_topic(command)

        if topic:
            search_wikipedia(topic)
        else:
            speak("Please say what you want me to search.")
            second_try = listen_command()
            if second_try:
                topic = extract_topic("tell me about " + second_try)
                if topic:
                    search_wikipedia(topic)
                else:
                    speak("Still couldn't get the topic. Try again.")

if __name__ == "__main__":
    main()
