from queue import Queue, Empty
from threading import Thread, Event
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from typing import Iterator

from piper import PiperVoice
import sounddevice as sd

from utils import logger, OrionEngineException


LOGGING_NAME = '[TTSManager]'


# ----------------------------
# Abstract base classes
# ----------------------------
class BaseAudioPlayer(ABC):
    @abstractmethod
    def play(self, chunk) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
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
    PLAYING = 1
    INTERRUPTED = 2
        

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
        voices_dir: str = 'voice_engine/voices',
        use_cuda: bool = False,
        frame_size: int = 2048
    ) -> None:
        super().__init__()
        voice_path = Path(voices_dir) / f'{voice}.onnx'
        self.voice = PiperVoice.load(
            voice_path, 
            use_cuda= use_cuda
        )
        self.frame_size = frame_size

    @property
    def sample_rate(self) -> int:
        return self.voice.config.sample_rate

    def synthesize(self, text: str) -> Iterator:
        for chunk in self.voice.synthesize(text):
            chunk_arr = chunk.audio_int16_array

            for i in range(0, len(chunk_arr), self.frame_size):
                yield chunk_arr[i:i+self.frame_size]


# ----------------------------
# Manager
# ----------------------------
class TTSManager:
    _STOP = object()
    _END_OF_REQUEST = object()

    def __init__(
        self,
        synthesizer: BaseSynthesizer,
        audio_player: BaseAudioPlayer,
        *,
        request_buffer_size: int = 5,
        audio_buffer_size: int = 25
    ) -> None:
        self.synthesizer = synthesizer
        self.audio_player = audio_player

        self.request_queue = Queue(maxsize= request_buffer_size)
        self.audio_queue = Queue(maxsize= audio_buffer_size)

        self.state = TTSState.IDLE
        self.interruptable_current_request = True
        self.stop_event = Event()

        self.request_worker = Thread(
            target= self.__synthesis_loop
        )
        self.audio_worker = Thread(
            target= self.__playback_loop
        )

        self.request_worker.start()
        self.audio_worker.start()

        logger.info(f'{LOGGING_NAME} Initialized Successfully. SYNTHESIZER = {self.synthesizer.__class__.__name__}, AUDIO_PLAYER = {self.audio_player.__class__.__name__}')

    def say(
        self,
        text: str,
        *,
        interrupt: bool = True
    ):
        logger.info(f'{LOGGING_NAME} Request Recieved. text={text[:80]!r}, {interrupt=}')
        self.request_queue.put(
            SpeechRequest(
                text, 
                interrupt
            )
        )

    def interrupt(self):
        if self.interruptable_current_request:
            logger.info(f'{LOGGING_NAME} Interrupted.')
            self.stop_event.set()
            self.state = TTSState.INTERRUPTED
            self.__clear_queue(self.audio_queue)
            self.__clear_queue(self.request_queue)

    def shutdown(self):
        self.request_queue.put(self._STOP)
        self.audio_queue.put(self._STOP)

        self.request_worker.join()
        self.audio_worker.join()

        self.audio_player.stop()
        logger.info(f'{LOGGING_NAME} Shutting Down.')

    @property
    def is_speaking(self) -> bool:
        return self.state == TTSState.PLAYING

    @staticmethod
    def __clear_queue(queue: Queue):
        while True:
            try:
                queue.get_nowait()

            except Empty:
                break

    def __synthesis_loop(self):
        while True:
            try:
                request = self.request_queue.get()
                if request is self._STOP:
                    self.audio_queue.put(self._STOP)
                    break

                logger.debug(f'{LOGGING_NAME} Synthesis started for {len(request.text)} chars.')

                self.stop_event.clear()
                self.interruptable_current_request = request.interrupt

                for chunk in self.synthesizer.synthesize(request.text):
                    if request.interrupt and self.stop_event.is_set():
                        logger.debug(f'{LOGGING_NAME} Synthesis Interrupted.')
                        break

                    self.audio_queue.put(chunk)
                self.audio_queue.put(self._END_OF_REQUEST)
                logger.debug(f'{LOGGING_NAME} Synthesis Completed.')

            except Exception as e:
                raise OrionEngineException(f'{LOGGING_NAME} Synthesis worker crashed: {e}')

    def __playback_loop(self):
        while True:
            try:
                chunk = self.audio_queue.get()
                if chunk is self._STOP:
                    break

                if chunk is self._END_OF_REQUEST:
                    logger.debug(f'{LOGGING_NAME} Playback Finished.')
                    self.state = (
                        TTSState.IDLE 
                        if self.state != TTSState.INTERRUPTED else 
                        TTSState.INTERRUPTED
                    )
                    continue

                if self.stop_event.is_set():
                    continue

                if self.state != TTSState.PLAYING:
                    logger.debug(f'{LOGGING_NAME} Playback Started.')

                self.state = TTSState.PLAYING
                self.audio_player.play(chunk)

            except Exception as e:
                raise OrionEngineException(f'{LOGGING_NAME} Playback worker crashed: {e}')
