#!/usr/bin/env python

import wave
import gtts
import pyaudio
import speech_recognition as sr
from playsound import playsound
from deep_translator import GoogleTranslator

"""

Simple translator using Google services

"""


class Translator:
    def __init__(self, chunk: int = 1024, audio_format=pyaudio.paInt16, channel: int = 1, rate: int = 44100):
        """

        Constructor

        :param chunk: chunk
        :type chunk: int
        :param audio_format: records audio format
        :type audio_format: int
        :param channel: alsa channel
        :type channel: int
        :param rate: audio rate
        :type rate: int
        """
        self._chunk = chunk
        self._format = audio_format
        self._channel = channel
        self._sample_rate = rate

    def record_file(self, file_name: str = 'recorded.wav', record_seconds: int = 5):
        """

        Record form microphone to file

        :param file_name: output file name
        :type file_name: str
        :param record_seconds: record time in seconds
        :type record_seconds: int
        """
        p = pyaudio.PyAudio()
        stream = p.open(format=self._format, channels=self._channel, rate=self._sample_rate,
                        input=True, output=True, frames_per_buffer=self._chunk)
        frames = []
        print("Recording...")
        for i in range(int(44100 / self._chunk * record_seconds)):
            data = stream.read(self._chunk)
            frames.append(data)
        print("Finished recording.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf = wave.open(file_name, "wb")
        wf.setnchannels(self._channel)
        wf.setsampwidth(p.get_sample_size(self._format))
        wf.setframerate(self._sample_rate)
        wf.writeframes(b"".join(frames))
        wf.close()

    @staticmethod
    def play_file(file_name: str = 'recorded.wav'):
        """

        Play audio file

        :param file_name: file name
        :type file_name: str
        """
        playsound(file_name)

    @staticmethod
    def recognize_file(file_name: str = 'recorded.wav', language: str = 'ru') -> str:
        """

        Recognize audio file

        :param file_name: file name
        :type file_name: str
        :param language: source language
        :type language: str
        :return: recognized text
        :rtype: str
        """
        recognizer = sr.Recognizer()
        input_file = sr.AudioFile(file_name)
        with input_file as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.record(source)
            result = recognizer.recognize_google(audio, language=language)
        return result

    @staticmethod
    def translate_text(input_text: str, source='auto', target='en') -> str:
        """

        Text translator

        :param input_text: source text
        :type input_text: str
        :param source: source language
        :type source: str
        :param target: target language
        :type target: str
        :return: translated text
        :rtype: str
        """
        return GoogleTranslator(source=source, target=target).translate(input_text)

    @staticmethod
    def text_to_file(input_text: str, file_name: str = 'translated.mp3', language='en'):
        """

        Converting text to audio file

        :param input_text: source text
        :type input_text: str
        :param file_name: file name
        :type file_name: str
        :param language: source language
        :type language: str
        """
        gtts.gTTS(input_text, lang=language).save(file_name)


"""

Test (from command line: ./main.py 2>/dev/null)

"""

if __name__ == '__main__':
    seconds = 10
    print('Started')
    translator = Translator()
    print(f'Recording {seconds} seconds...')
    translator.record_file(record_seconds=seconds)
    print('Recorded')
    print('Playing recorded...')
    translator.play_file()
    print('Recognizing...')
    recognized = translator.recognize_file()
    print(f'Recognized: \'{recognized}\'')
    print('Translating...')
    translated = translator.translate_text(recognized)
    print(f'Translated: \'{translated}\'')
    print('Saving translated to audio file...')
    translator.text_to_file(translated)
    print('Saved')
    print('Playing saved...')
    translator.play_file('translated.mp3')
    print('Finished')
