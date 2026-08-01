from queue import Queue, Empty
from threading import Thread, Event
from abc import ABC, abstractmethod
from typing import Iterator, Literal
from enum import Enum
from dataclasses import dataclass

import sounddevice as sd
import silero_vad as silero
from faster_whisper import WhisperModel
import numpy as np
import torch

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
    def detect(self, chunk) -> dict[str, int | float] | None:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...


class BaseRecognizer(ABC):
    @abstractmethod
    def recognize(self, audio) -> Iterator:
        ...


# ----------------------------
# Helper Classes
# ----------------------------
@dataclass
class TextRequest:
    audio: np.ndarray
    interrupt: bool


class STTState(Enum):
    IDLE = 0
    PLAYING = 1
    INTERRUPTED = 2


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

    def record(self, *, frames: int = 512):
        audio, _ = self.stream.read(frames)
        return audio

    def stop(self) -> None:
        self.stream.stop()
        self.stream.close()


# ----------------------------
# Voice Activity Detector
# ----------------------------
class SileroVAD(BaseVAD):
    def __init__(self, **vad_kwargs):
        super().__init__()
        self.model = silero.load_silero_vad()
        self.iterator = silero.VADIterator(
            model= self.model,
            **vad_kwargs
        )

    def detect(self, chunk: np.ndarray):
        # preprocessing
        chunk = chunk.squeeze()     # (C, 1) -> (C,)
        norm_factor = -np.iinfo(np.int16).min
        chunk = chunk.astype(np.float32) / norm_factor
        chunk = torch.from_numpy(chunk)

        return self.iterator(chunk)

    def reset(self):
        self.iterator.reset_states()


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
        super().__init__()
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
    _STOP = object()
    _END_OF_REQUEST = object()

    def __init__(
        self, 
        recorder: BaseRecorder,
        vad: BaseVAD,
        recognizer: BaseRecognizer,
        *,
        request_buffer_size: int = 5,
        vad_buffer_size: int = 25, 
        recognizer_buffer_size: int = 25
    ) -> None:
        self.recorder = recorder
        self.vad = vad
        self.recognizer = recognizer

        self.request_queue = Queue(maxsize= request_buffer_size)
        self.vad_queue = Queue(maxsize= vad_buffer_size)
        self.recognizer_queue = Queue(maxsize= recognizer_buffer_size)

        self.state = STTState.IDLE
        self.interruptable_current_request = True
        self.stop_event = Event()

        self.request_worker = Thread(target= self.__recorder_loop)
        self.vad_worker = Thread(target= self.__vad_loop)
        self.recognize_worker = Thread(target= self.__recognize_loop)

        self.request_worker.start()
        self.vad_worker.start()
        self.recognize_worker.start()

        logger.info(f'STTManager has been initialized. Recorder = {self.recorder.__class__.__name__}, vad = {self.vad.__class__.__name__}, recognizer = {self.recognizer.__class__.__name__}')

    def listen(
        self, 
        audio,
        *,
        interrupt: bool = True
    ):
        logger.info('STT request recieved')
        self.request_queue.put(
            TextRequest(
                audio= audio,
                interrupt= interrupt
            )
        )

    def interrupt(self):
        if self.interruptable_current_request:
            logger.info('STT Interrupted')
            self.stop_event.set()
            self.state = STTState.INTERRUPTED
            self.vad.reset()
            self.__clear_queue(self.request_queue)
            self.__clear_queue(self.vad_queue)
            self.__clear_queue(self.recognizer_queue)

    def shutdown(self):
        logger.info('Shutting down STT')
        self.request_queue.put(self._STOP)
        self.vad_queue.put(self._STOP)
        self.recognizer_queue.put(self._STOP)

        self.request_worker.join()
        self.vad_worker.join()
        self.recognize_worker.join()

        self.recorder.stop()

    @staticmethod
    def __clear_queue(queue: Queue):
        while True:
            try:
                queue.get_nowait()

            except Empty:
                break

    def __recorder_loop(self) -> None:
        ...

    def __vad_loop(self) -> None:
        ...

    def __recognize_loop(self) -> None:
        ...
