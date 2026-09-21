from queue import Queue
from collections import deque
from threading import Thread, Event
from abc import ABC, abstractmethod
from typing import Literal, Iterable

import sounddevice as sd
import silero_vad as silero
from faster_whisper import WhisperModel
import numpy as np
import torch

from utils import logger, OrionEngineException


LOGGING_NAME = '[STTManager]'


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
    def detect(self, chunk: np.ndarray) -> dict[str, int | float] | None:
        ...

    @abstractmethod
    def reset(self) -> None:   # mainly required when creating a new session, or switching audio source
        ...

    @abstractmethod
    def check_start(self, detection: dict | None) -> bool:
        ...

    @abstractmethod
    def check_end(self, detection: dict | None) -> bool:
        ...


class BaseRecognizer(ABC):
    @abstractmethod
    def recognize(self, audio) -> Iterable:
        ...


# ----------------------------
# Recorder
# ----------------------------
class SoundDeviceRecorder(BaseRecorder):
    """Record audio from an input device using SoundDevice."""
    def __init__(
        self, 
        *, 
        samplerate: int = 16_000, 
        frames: int = 512
    ) -> None:
        """Initialize and start the audio input stream.

        Args:
            samplerate: Number of audio samples captured per second.
            frames: Number of audio frames read per recording operation.
        """
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
        """Read and return the next audio chunk from the input stream."""
        audio, _ = self.stream.read(self.frames)
        return audio

    def stop(self) -> None:
        """Stop and close the audio input stream.""" 
        self.stream.stop()
        self.stream.close()


# ----------------------------
# Voice Activity Detector
# ----------------------------
class SileroVAD(BaseVAD):
    """Detect voice activity in audio using Silero VAD."""
    def __init__(self, **vad_kwargs):
        super().__init__()
        self.model = silero.load_silero_vad()
        self.iterator = silero.VADIterator(
            model= self.model,
            **vad_kwargs
        )

    def detect(self, chunk: np.ndarray) -> dict[str, int | float] | None:
        """Analyze an audio chunk and detect voice activity."""
        # preprocessing
        chunk = chunk.squeeze()     # (C, 1) -> (C,)
        chunk = chunk.astype(np.float32) / 32768.0
        chunk = torch.from_numpy(chunk)

        return self.iterator(chunk)

    def reset(self) -> None:
        """Reset the VAD state for a new audio sequence."""
        self.iterator.reset_states()

    def __check(self, detection: dict | None, word: str) -> bool:
        """Check whether a VAD detection matches the specified event."""
        if detection is None:
            return False

        key = next(iter(detection))
        return key == word

    def check_start(self, detection: dict | None) -> bool:
        """Check whether a detection indicates the start of speech."""
        return self.__check(detection, 'start')

    def check_end(self, detection: dict | None) -> bool:
        """Check whether a detection indicates the end of speech."""
        return self.__check(detection, 'end')


# ----------------------------
# Recognizer
# ----------------------------
class FasterWhisperRecognizer(BaseRecognizer):
    """Recognize speech from audio using a Faster Whisper model."""
    def __init__(
        self,
        *, 
        model: Literal['tiny.en', 'base.en', 'small.en'] = 'base.en',
        language: str = 'en',
        compute_type: str = 'auto'
    ) -> None:
        """Initialize the speech recognition model.

        Args:
            model: The Faster Whisper model size to use.
            language: Language expected in the input audio.
            compute_type: Computation type used by the model.
        """
        super().__init__()
        self.language = language
        self.model = WhisperModel(
            model_size_or_path= model,
            compute_type= compute_type
        )

    def recognize(self, audio) -> Iterable:
        """Transcribe the provided audio into speech segments."""
        segments, _ = self.model.transcribe(
            audio,
            language= self.language,
            beam_size= 5,
            vad_filter= False
        )
        return segments


# ----------------------------
# Manager
# ----------------------------
class STTManager:
    """Manage the audio recording, voice detection, and speech recognition pipeline.

    Coordinates audio capture, voice activity detection, and speech-to-text
    processing using separate worker threads and queues.
    """
    _STOP = object()

    def __init__(
        self, 
        *,
        model: str = 'base.en',
        audio_buffer_size: int = 25,
        utterance_buffer_size: int = 25, 
        transcript_buffer_size: int = 25
    ) -> None:
        """Initialize the speech-to-text pipeline and start its workers.

        Args:
            model: Speech recognition model to use.
            audio_buffer_size: Maximum number of audio chunks held for voice activity detection.
            utterance_buffer_size: Maximum number of detected utterances waiting for recognition.
            transcript_buffer_size: Maximum number of recognized transcripts waiting to be retrieved.
        """
        # main attributes
        self.recorder = SoundDeviceRecorder()
        self.vad = SileroVAD()
        self.recognizer = FasterWhisperRecognizer(
            model= model
        )

        self.audio_queue = Queue(maxsize= audio_buffer_size)
        self.utterance_queue = Queue(maxsize= utterance_buffer_size)
        self.transcript_queue = Queue(maxsize= transcript_buffer_size)

        # threads
        self.stop_event = Event()
        self.listening_event = Event()

        self.record_worker = Thread(target= self.__recorder_loop)
        self.vad_worker = Thread(target= self.__vad_loop)
        self.recognize_worker = Thread(target= self.__recognize_loop)

        self.record_worker.start()
        self.vad_worker.start()
        self.recognize_worker.start()

        logger.info(f'{LOGGING_NAME} Initialized Successfully. RECORDER: {self.recorder.__class__.__name__}, VAD: {self.vad.__class__.__name__}, RECOGNIZER: {self.recognizer.__class__.__name__}')

    def start_listening(self) -> None:
        """Start capturing and processing incoming audio."""
        logger.info(f'{LOGGING_NAME} Started Listening.')
        self.listening_event.set()

    def stop_listening(self) -> None:
        """Stop capturing new audio while keeping the pipeline running."""
        logger.info(f'{LOGGING_NAME} Stopped Listening.')
        self.listening_event.clear()

    def get_transcript(self) -> str:
        """Retrieve the next available speech transcript."""
        return self.transcript_queue.get()

    @property
    def is_listening(self) -> bool:
        """Return whether the manager is currently listening for speech."""
        return self.listening_event.is_set()

    def shutdown(self) -> None:
        """Stop all workers and release the audio processing resources."""
        self.stop_event.set()
        self.listening_event.set()

        self.record_worker.join()
        self.vad_worker.join()
        self.recognize_worker.join()

        self.recorder.stop()
        self.vad.reset()
        logger.info(f'{LOGGING_NAME} Shutting Down.')

    def __recorder_loop(self) -> None:
        """Continuously capture audio chunks while listening is enabled."""
        while True:
            try:
                self.listening_event.wait()

                if self.stop_event.is_set():
                    self.audio_queue.put(self._STOP)
                    break

                audio_chunk = self.recorder.record()
                self.audio_queue.put(audio_chunk)

            except Exception as e:
                raise OrionEngineException(f'{LOGGING_NAME} Recorder worker crashed: {e}')

    def __vad_loop(self) -> None:
        """Detect speech activity and assemble complete speech utterances."""
        speech_buffer = []
        recording = False
        history = deque(maxlen= 5)

        # silero vad only gives where audio starts and ends, so building audio chunk based on this
        while True:
            try:
                chunk = self.audio_queue.get()

                if chunk is self._STOP:
                    self.utterance_queue.put(self._STOP)
                    break

                result = self.vad.detect(chunk)

                if not recording:
                    history.append(chunk)

                    if self.vad.check_start(result):
                        logger.debug(f'{LOGGING_NAME} Activity Detected.')
                        speech_buffer.extend(history)
                        history.clear()
                        recording = True

                else:
                    speech_buffer.append(chunk)

                    if self.vad.check_end(result):
                        logger.debug(f'{LOGGING_NAME} Activity Ended.')

                        audio = np.concatenate(speech_buffer, axis= 0)
                        audio = audio[:, 0].astype(np.float32) / 32768.0
                        audio = np.ascontiguousarray(audio)

                        self.utterance_queue.put(audio)
                        speech_buffer.clear()
                        history.clear()

                        recording = False
                        self.vad.reset()

            except Exception as e:
                raise OrionEngineException(f'{LOGGING_NAME} VAD worker crashed: {e}')

    def __recognize_loop(self) -> None:
        """Transcribe detected speech utterances and queue their transcripts."""
        while True:
            try:
                audio = self.utterance_queue.get()

                if audio is self._STOP:
                    break

                # used to debug, but no longer needed
                logger.debug(
                    f'Audio dtype={audio.dtype}, '
                    f'shape={audio.shape}, '
                    f'min={audio.min()}, '
                    f'max={audio.max()}, '
                    f'duration={len(audio) / 16000:.2f}s'
                )

                segments = list(self.recognizer.recognize(audio))
                logger.debug(f'{LOGGING_NAME} Segments Generated: {len(segments)}')

                transcript = ''.join(
                    segment.text
                    for segment in segments
                )
                logger.debug(f'{LOGGING_NAME} Transcript: {transcript}')
                self.transcript_queue.put(transcript)

            except Exception as e:
                raise OrionEngineException(f'{LOGGING_NAME} Recognize worker crashed: {e}')
