from abc import ABC, abstractmethod
import sounddevice as sd
from pysilero_vad import SileroVoiceActivityDetector
import faster_whisper as fw


# ----------------------------
# Abstract base classes
# ----------------------------
class BaseRecorder(ABC):
    ...


class BaseVAD(ABC):
    ...


class BaseRecognizer(ABC):
    ...


# ----------------------------
# Recorder
# ----------------------------
class MicrophoneRecorder(BaseRecorder):
    ...


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