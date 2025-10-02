from mqttAWS import init_mqtt, sendToESP
import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import pyttsx3

#----------------- Audio --------------------
Device = None
SAMPLERATE = 16000
buffer = queue.Queue()

def audioCallback(indata, frames, time, status):
    buffer.put(bytes(indata))


#------------------ Text to speech ----------------
def speak(text):
    print("Assistant:", text)
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('voice', engine.getProperty('voices')[1].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("TTS Error:", e)


#------------------ Vosk Model ----------------
model_path = "vosk-model-small-en-us-0.15"
model = Model(model_path)

#------------------ Command Handling ----------------
def handleCommand(text):
    if text == "system":
        speak("""Welcome to the Dari System. Your smart home assistant. 
                 You can ask me if someone is at home, tell me to open or close the door or 
                 turn the light on or off, or ask me about the temperature.""")

    elif text == "is anyone there":
        response = sendToESP("status")
        if isinstance(response, dict):
            status = response.get("response", "").lower()
            if "someone" in status:
                speak("Yes, someone is there.")
            else:
                speak("No, no one's there.")
        else:
            speak("Failed to get status.")
            
    elif text == "open the door":
        response = sendToESP("open")
        if isinstance(response, dict):
            if response.get("response") == "opened":
                speak("The door is now open.")
            else:
                speak("Failed to open the door.")
        else:
            speak("Failed to open the door.")


    elif text == "close the door":
        response = sendToESP("close")
        if isinstance(response, dict):
            if response.get("response") == "closed":
                speak("The door is now closed.")
            else:
                speak("Failed to close the door.")
        else:
            speak("Failed to close the door.")

    elif text == "turn on the light":
        response = sendToESP("turn on")
        if isinstance(response, dict):
            if response.get("response") == "light on":
                speak("The light is now on.")
            else:
                speak("Failed to turn on the light.")
        else:
            speak("Failed to turn on the light.")
            
    elif text == "turn off the light":
        response = sendToESP("turn off")
        if isinstance(response, dict):
            if response.get("response") == "light off":
                speak("The light is now off.")
            else:
                speak("Failed to turn off the light.")
        else:
            speak("Failed to turn off the light.")
            
    elif text == "temperature":
        response = sendToESP("indoor climate")   
        if isinstance(response, dict):
            temp = response.get("temperature")
            humidity = response.get("humidity")
            if temp is not None and humidity is not None:
                speak(f"The indoor temperature is {temp}°C with {humidity}% Humidity")
            else:
                speak("Failed to read temperature and humidity.")
        else:
            speak("Failed to get indoor climate.")
        
    elif text == "thank you":
        speak("Your welcome , i'm here if you need any help just say system or exit if you need to exit")
        
        
    elif text == "exit":
        speak("See you soon!")
        exit(0)
        
    else:
        speak("Sorry, can you repeat?")


#------------------ Main Program ----------------
def main():
    with sd.RawInputStream(samplerate=SAMPLERATE, device=Device, blocksize=8000,
                           channels=1, dtype='int16', callback=audioCallback) as stream:
        recognizer = KaldiRecognizer(model, SAMPLERATE)
        print("Listening ...")

        while True:
            data = buffer.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    print(f"You said: {text}")
                    handleCommand(text)



if __name__ == "__main__":
    init_mqtt()
    main()
