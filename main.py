#!/usr/bin/env python

import math
import wave
import gtts
import struct
import pyaudio
import threading
import speech_recognition as sr
import speech_recognition.exceptions
from playsound import playsound
from deep_translator import GoogleTranslator

"""

Simple translator using Google services

"""


class Translator:
    def __init__(self, chunk: int = 1024, audio_format=pyaudio.paInt16, channel: int = 1, pause: int = 2,
                 rate: int = 44100, normalize: float = (1.0/32768.0), noise: float = 0.04521571580107228,
                 debug: bool = False):
        """

        Constructor

        :param chunk: chunk
        :type chunk: int
        :param audio_format: records audio format
        :type audio_format: int
        :param channel: alsa channel
        :type channel: int
        :param pause: pause in sec (start translate)
        :type pause: int
        :param rate: audio rate
        :type rate: int
        :param debug: debug
        :type debug: bool
        :param normalize: normalization
        :type normalize: float
        """
        self._chunk = chunk
        self._format = audio_format
        self._channel = channel
        self._sample_rate = rate
        self._normalize = normalize
        self._noise = noise
        self._pause = pause
        self._debug = debug

    def record_file(self, file_name: str = 'recorded.wav', record_seconds: int = 5) -> bool:
        """

        Record form microphone to file

        :param file_name: output file name
        :type file_name: str
        :param record_seconds: record time in seconds
        :type record_seconds: int
        :return True if recorded data
        :rtype: bool
        """
        p = pyaudio.PyAudio()
        stream = p.open(format=self._format, channels=self._channel, rate=self._sample_rate,
                        input=True, output=True, frames_per_buffer=self._chunk)
        frames = []
        recorded = False
        empty_counter = 0
        max_wakeup_amplitude = 0.0
        for i in range(int(self._sample_rate / self._chunk * record_seconds)):
            data = stream.read(self._chunk)
            amplitude = self.get_amplitude(data)
            if amplitude < self._noise:
                empty_counter += 1
                if not recorded and empty_counter == 1 and self._debug:
                    print('Speak, please...')
            else:
                empty_counter = 0
                recorded = True
                if self._debug:
                    print(f'Wake amplitude {amplitude}')
                if amplitude > max_wakeup_amplitude:
                    max_wakeup_amplitude = amplitude
            if empty_counter >= int(self._sample_rate / self._chunk * self._pause):
                break
            frames.append(data)
        if self._debug:
            print("Finished recording.")
            print(f'Max wakeup amplitude {max_wakeup_amplitude}')
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf = wave.open(file_name, "wb")
        wf.setnchannels(self._channel)
        wf.setsampwidth(p.get_sample_size(self._format))
        wf.setframerate(self._sample_rate)
        wf.writeframes(b"".join(frames))
        wf.close()
        return recorded

    def get_amplitude(self, block):
        """

        Get block amplitude

        :param block: data
        :type block: bytes
        :return: amplitude
        :rtype: float
        """
        count = len(block) / 2
        shorts = struct.unpack("%dh" % count, block)
        sum_squares = 0.0
        for sample in shorts:
            n = sample * self._normalize
            sum_squares += n * n
        return math.sqrt(sum_squares / count)

    def translate(self, source_file: str = 'recorded.wav', target_file: str = 'translated.mp3',
                  source: str = 'ru', target='en'):
        """

        Translate file

        :param source_file: source file
        :param target_file: translated file
        :param source: source language
        :param target: target language
        """
        try:
            recognized = self.recognize_file(source_file, source)
            if self._debug:
                print(f'Recognized: \'{recognized}\'')
                print('Translating...')
            translated = self.translate_text(recognized, target=target)
            if self._debug:
                print(f'Translated: \'{translated}\'')
                print('Saving translated to audio file...')
            self.text_to_file(translated, file_name=target_file, language=target)
            if self._debug:
                print('Saved')
                print('Playing saved...')
            self.play_file('translated.mp3')
        except speech_recognition.exceptions.UnknownValueError:
            if self._debug:
                print('Silence')

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
    seconds = 3600
    translator = Translator()
    while True:
        if translator.record_file(record_seconds=seconds):
            t = threading.Thread(target=translator.translate)
            t.daemon = False
            t.start()
