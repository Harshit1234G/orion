from queue import Queue
from threading import Thread, Event
from abc import ABC, abstractmethod
from typing import Iterator, Literal
from enum import Enum

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
    def record(self) -> np.ndarray:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


class BaseVAD(ABC):
    @abstractmethod
    def detect(self, chunk) -> dict[str, int | float] | None:
        ...

    @abstractmethod
    def reset(self) -> None:   # mainly required when creating a new session, or switching audio source
        ...


class BaseRecognizer(ABC):
    @abstractmethod
    def recognize(self, audio) -> Iterator:
        ...


# ----------------------------
# Helper Classes
# ----------------------------
class STTState(Enum):
    IDLE = 0
    RECORDING = 1


# ----------------------------
# Recorder
# ----------------------------
class SoundDeviceRecorder(BaseRecorder):
    def __init__(
        self, 
        *, 
        samplerate: int = 16_000, 
        frames: int = 512
    ) -> None:
        super().__init__()
        self.frames = frames
        self.stream = sd.InputStream(
            samplerate= samplerate,
            blocksize= 0,
            channels= 1,
            dtype= 'int16',
            latency= 'low'
        )
        self.stream.start()

    def record(self) -> np.ndarray:
        audio, _ = self.stream.read(self.frames)
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
    def __init__(
        self, 
        recorder: BaseRecorder,
        vad: BaseVAD,
        recognizer: BaseRecognizer,
        *,
        recorder_buffer_size: int = 25,
        vad_buffer_size: int = 25, 
        transcript_buffer_size: int = 25
    ) -> None:
        self.recorder = recorder
        self.vad = vad
        self.recognizer = recognizer

        self.recorder_queue = Queue(maxsize= recorder_buffer_size)
        self.vad_queue = Queue(maxsize= vad_buffer_size)
        self.transcript_queue = Queue(maxsize= transcript_buffer_size)

        self.state = STTState.IDLE
        self.stop_event = Event()

        self.record_worker = Thread(target= self.__recorder_loop)
        self.vad_worker = Thread(target= self.__vad_loop)
        self.recognize_worker = Thread(target= self.__recognize_loop)

        self.record_worker.start()
        self.vad_worker.start()
        self.recognize_worker.start()

        logger.info(f'STTManager has been initialized. Recorder = {self.recorder.__class__.__name__}, vad = {self.vad.__class__.__name__}, recognizer = {self.recognizer.__class__.__name__}')

    def start_listening(self):
        self.state = STTState.RECORDING

    def stop_listening(self):
        self.state = STTState.IDLE

    @property
    def is_listening(self):
        return self.state == STTState.RECORDING

    def shutdown(self):
        logger.info('Shutting down STT')
        self.stop_event.set()

        self.record_worker.join()
        self.vad_worker.join()
        self.recognize_worker.join()

        self.recorder.stop()
        self.vad.reset()

    def __recorder_loop(self) -> None:
        while True:
            try:
                if self.stop_event.is_set():
                    break

                if self.is_listening:
                    audio_chunk = self.recorder.record()
                    self.recorder_queue.put(audio_chunk)

            except Exception as e:
                logger.error(f'Recorder worker crashed: {e}')
                raise

    def __vad_loop(self) -> None:
        ...

    def __recognize_loop(self) -> None:
        ...
