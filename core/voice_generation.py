from queue import Queue
from threading import Thread
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from piper import PiperVoice
import sounddevice as sd


# Abstract base classes
class BaseAudioPlayer(ABC):
    ...


class BaseSynthesizer(ABC):
    ...


# helper classes
@dataclass
class SpeechRequest:
    text: str
    priority: int
    interrupt: bool


class TTSState(Enum):
    IDLE = 0
    SYNTHESIZING = 1
    PLAYING = 2
    INTERRUPTED = 3
        

class SoundDevicePlayer(BaseAudioPlayer):
    ...


class PiperSynthesizer(BaseSynthesizer):
    ...


class PiperVoiceThreadedTTS:
    def __init__(
        self, 
        voice: str, 
        *, 
        voices_dir: str = 'voices', 
        use_cuda: bool = False,
        queue_size: int = 0
    ) -> None:
        # Voice
        voice_path = Path(voices_dir) / f'{voice}.onnx'
        self.voice = PiperVoice.load(voice_path, use_cuda= use_cuda)

        # queue and other attributes
        self.request_queue = Queue(maxsize= queue_size)
        self.audio_queue = Queue(maxsize= queue_size)
        self._STOP = object()
        self._END_OF_SENTENCE = object()

        # threads
        self.request_worker = Thread(target= self.__synthesize)
        self.audio_worker = Thread(target= self.__playback)
        self.request_worker.start()
        self.audio_worker.start()

    def __synthesize(self):
        while True:
            try:
                request = self.request_queue.get()

                if request is self._STOP:
                    break

                for audio_chunk in self.voice.synthesize(request.text):
                    self.audio_queue.put(audio_chunk.audio_int16_array)

                self.audio_queue.put(self._END_OF_SENTENCE)

            except Exception as e:
                print(e)    # TODO: Change exception handling, with logging or UI related

    def __playback(self):
        stream = sd.OutputStream(
            samplerate= self.voice.config.sample_rate,
            channels= 1,
            dtype= 'int16',
            blocksize= 0,
            latency= 'low'
        )
        stream.start()

        while True:
            chunk = self.audio_queue.get()

            if chunk is self._END_OF_SENTENCE:    #! Might not work as expected
                break

            stream.write(chunk)

        stream.stop()
        stream.close()


    def __tts_worker(self) -> None:
        stream = sd.OutputStream(
            samplerate= self.voice.config.sample_rate,
            channels= 1,
            dtype= 'int16',
            blocksize= 0,
            latency= 'low'
        )
        stream.start()
    
        while True:
            try:
                request = self.queue.get()
        
                if request is self._STOP:
                    break
        
                for audio_chunk in self.voice.synthesize(request.text):
                    if self.stop_requested and request.interrupt:
                        break
                    stream.write(audio_chunk.audio_int16_array)

            except Exception as e:
                print(e)
    
        stream.stop()
        stream.close()

    # wrapper / helper function for simple calling of tts
    def say(
        self, 
        text: str, 
        *,
        interrupt: bool = True
    ) -> None:
        request = SpeechRequest(text, interrupt)
        self.request_queue.put(request)

    def stop(self) -> None:
        self.request_queue.put(self._STOP)
        self.audio_worker.join()
        self.request_worker.join()
