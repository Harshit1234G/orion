from queue import Queue, Empty
from threading import Thread, Event
from abc import ABC, abstractmethod
from typing import Iterator, Literal

import sounddevice as sd
from pysilero_vad import SileroVoiceActivityDetector
from faster_whisper import WhisperModel

from utils import logger


# ----------------------------
# Abstract base classes
# ----------------------------
class BaseRecorder(ABC):
    @abstractmethod
    def record(self, frames: int):
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


class BaseVAD(ABC):
    @abstractmethod
    def detect(self, audio) -> None:
        ...


class BaseRecognizer(ABC):
    @abstractmethod
    def recognize(self, audio) -> Iterator:
        ...


# ----------------------------
# Recorder
# ----------------------------
class SoundDeviceRecorder(BaseRecorder):
    def __init__(self, *, samplerate: int = 16_000) -> None:
        super().__init__()
        self.stream = sd.InputStream(
            samplerate= samplerate,
            blocksize= 0,
            channels= 1,
            dtype= 'int16',
            latency= 'low'
        )
        self.stream.start()

    def record(self, frames: int):
        audio, _ = self.stream.read(frames)
        return audio

    def stop(self) -> None:
        self.stream.stop()
        self.stream.close()


# ----------------------------
# Voice Activity Detector
# ----------------------------
class SileroVAD(BaseVAD):
    ...


# ----------------------------
# Recognizer
# ----------------------------
class FasterWhisperRecognizer(BaseRecognizer):
    def __init__(
        self,
        *, 
        model: Literal['tiny.en', 'base.en', 'small.en'] = 'base.en',
        language: str = 'en',
        compute_type: str = 'int8'   # quantization for cpu
    ) -> None:
        self.language = language
        self.model = WhisperModel(
            model_size_or_path= model,
            compute_type= compute_type
        )

    def recognize(self, audio) -> Iterator:
        segments, _ = self.model.transcribe(
            audio,
            language= self.language
        )
        return segments


# ----------------------------
# Manager
# ----------------------------
class STTManager:
    ...