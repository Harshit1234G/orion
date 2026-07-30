from abc import ABC, abstractmethod
import sounddevice as sd
from pysilero_vad import SileroVoiceActivityDetector
import faster_whisper as fw


# ----------------------------
# Abstract base classes
# ----------------------------
class BaseRecorder(ABC):
    @abstractmethod
    def record(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


class BaseVAD(ABC):
    ...


class BaseRecognizer(ABC):
    ...


# ----------------------------
# Recorder
# ----------------------------
class SoundDeviceRecorder(BaseRecorder):
    def __init__(self, samplerate: int) -> None:
        self.stream = sd.InputStream(
            samplerate= samplerate,
            blocksize= 0,
            channels= 1,
            dtype= 'int16',
            latency= 'low'
        )
        self.stream.start()

    def record(self, chunk) -> None:
        self.stream.read(chunk)

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
    ...


# ----------------------------
# Manager
# ----------------------------
class STTManager:
    ...