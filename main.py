import pyaudio
import wave
import speech_recognition as sr
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_ENDPOINT = os.getenv('GEMINI_API_ENDPOINT')

def record_audio(output_filename, max_duration=10, sample_rate=44100, channels=1):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=channels,
                        rate=sample_rate, input=True,
                        frames_per_buffer=1024)
    frames = []

    print("Listening...")

    for _ in range(0, int(sample_rate / 1024 * max_duration)):
        data = stream.read(1024)
        frames.append(data)

    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

def audio_to_text(audio_filename, text_filename):
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_filename) as source:
        audio_data = recognizer.record(source, duration=None)

    try:
        text = recognizer.recognize_google(audio_data)
        print(f"Transcribed text: {text}")

        with open(text_filename, 'w') as file:
            file.write(text)
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    return None

def response_generation(user_cmd):
    print('Thinking...')
    headers = {
        'Content-Type': 'application/json'
    }
    params = {
        'key': GEMINI_API_KEY
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": user_cmd
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API_ENDPOINT, headers=headers, params=params, json=data)
        response.raise_for_status()
        response_data = response.json()

        print("Full response from Gemini API:")
        print(json.dumps(response_data, indent=2))

        if 'candidates' in response_data:
            response_text = response_data['candidates'][0]['content']['parts'][0]['text']
        else:
            print("Unexpected response structure")
            return None

        print(f"DAISY: {response_text}")
        return response_text
    except requests.exceptions.RequestException as e:
        print(f"Error generating response: {e}")
    except KeyError as e:
        print(f"KeyError: {e}. Response structure might have changed.")

    return None

def main():
    audio_file = "recording.wav"
    text_file = "transcription.txt"
    response_file = "response.txt"

    print("Recording audio...")
    record_audio(audio_file, max_duration=10)

    print("Converting audio to text...")
    user_command = audio_to_text(audio_file, text_file)

    if user_command:
        print(f"User command: {user_command}")

        print("Generating response...")
        response_text = response_generation(user_command)

        if response_text:
            print("Writing response to file...")
            try:
                with open(response_file, 'w') as file:
                    file.write(response_text)
                print("Response written to file.")
            except Exception as e:
                print(f"Error writing to file: {e}")
        else:
            print("No response generated.")
    else:
        print("No user command detected.")

if __name__ == "__main__":
    if os.path.exists("response.txt"):
        print("response.txt exists, will overwrite.")
    else:
        print("response.txt does not exist, will create new.")
        
    main()
