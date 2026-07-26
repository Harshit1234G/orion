from queue import Queue, Empty
from threading import Thread, Event
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from typing import Iterator
from piper import PiperVoice
import sounddevice as sd


# ----------------------------
# Abstract base classes
# ----------------------------
class BaseAudioPlayer(ABC):
    @abstractmethod
    def play(self, chunk) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


class BaseSynthesizer(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> Iterator:
        ...


# ----------------------------
# Helper classes
# ----------------------------
@dataclass
class SpeechRequest:
    text: str
    interrupt: bool


class TTSState(Enum):
    IDLE = 0
    SYNTHESIZING = 1
    PLAYING = 2
    INTERRUPTED = 3
        

# ----------------------------
# Audio Player
# ----------------------------
class SoundDevicePlayer(BaseAudioPlayer):
    def __init__(self, sample_rate: int):
        super().__init__()
        self.stream = sd.OutputStream(
            samplerate= sample_rate,
            channels= 1,
            dtype= 'int16',
            blocksize= 0,
            latency= 'low'
        )
        self.stream.start()

    def play(self, chunk) -> None:
        self.stream.write(chunk)

    def stop(self) -> None:
        self.stream.stop()
        self.stream.close()


# ----------------------------
# Audio Synthesizers
# ----------------------------
class PiperSynthesizer(BaseSynthesizer):
    def __init__(
        self, 
        voice: str, 
        *, 
        voices_dir: str = 'voices',
        use_cuda: bool = False
    ) -> None:
        super().__init__()
        voice_path = Path(voices_dir) / f'{voice}.onnx'
        self.voice = PiperVoice.load(
            voice_path, 
            use_cuda= use_cuda
        )

    @property
    def sample_rate(self) -> int:
        return self.voice.config.sample_rate

    def synthesize(self, text: str) -> Iterator:
        for chunk in self.voice.synthesize(text):
            yield chunk.audio_int16_array


# ----------------------------
# Manager
# ----------------------------
class TTSManager:
    _STOP = object()
    _END_OF_REQUEST = object()

    def __init__(
        self,
        synthesizer: BaseSynthesizer,
        audio_player: BaseAudioPlayer
    ) -> None:
        self.synthesizer = synthesizer
        self.audio_player = audio_player

        self.request_queue = Queue()
        self.audio_queue = Queue()

        self.state = TTSState.IDLE
        self.stop_event = Event()

        self.request_worker = Thread(
            target= self.__synthesis_loop
        )

        self.audio_worker = Thread(
            target= self.__playback_loop
        )

        self.request_worker.start()
        self.audio_worker.start()

    def __synthesis_loop(self):
        while True:
            request = self.request_queue.get()

            if request is self._STOP:
                self.audio_queue.put(self._STOP)
                break

            self.stop_event.clear()
            self.state = TTSState.SYNTHESIZING

            for chunk in self.synthesizer.synthesize(request.text):
                if request.interrupt and self.stop_event.is_set():
                    break

                self.audio_queue.put(chunk)

            self.audio_queue.put(self._END_OF_REQUEST)

    def __playback_loop(self):
        while True:
            chunk = self.audio_queue.get()

            if chunk is self._STOP:
                break

            if chunk is self._END_OF_REQUEST:
                if self.state != TTSState.INTERRUPTED:
                    self.state = TTSState.IDLE

                continue

            self.state = TTSState.PLAYING

            if self.stop_event.is_set():
                continue

            self.audio_player.play(chunk)
