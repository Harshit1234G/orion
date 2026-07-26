from queue import PriorityQueue, Empty
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
    priority: int
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

        self.request_queue = PriorityQueue()
        self.audio_queue = PriorityQueue()

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
        ...

    def __playback_loop(self):
        ...
