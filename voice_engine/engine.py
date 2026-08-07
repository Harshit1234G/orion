from .text_to_speech import (
    BaseSynthesizer,
    BaseAudioPlayer,
    SoundDevicePlayer,
    PiperSynthesizer,
    TTSManager,
)
from .speech_to_text import (
    BaseRecognizer,
    BaseRecorder,
    BaseVAD,
    SoundDeviceRecorder,
    FasterWhisperRecognizer,
    SileroVAD,
    STTManager,
)
from utils import logger


class VoiceEngine:
    def __init__(
        self,
        synthesizer: BaseSynthesizer | None = None,
        audio_player: BaseAudioPlayer | None = None,
        recognizer: BaseRecognizer | None = None,
        recorder: BaseRecorder | None = None,
        vad: BaseVAD | None = None
    ) -> None:
        if synthesizer is None:
            synthesizer = PiperSynthesizer(voice= 'en_US-joe-medium.onnx')

        if audio_player is None:
            audio_player = SoundDevicePlayer(sample_rate= synthesizer.sample_rate)

        if recognizer is None:
            recognizer = FasterWhisperRecognizer()

        if recorder is None:
            recorder = SoundDeviceRecorder()

        if vad is None:
            vad = SileroVAD()

        self.speech_to_text = STTManager(recorder, vad, recognizer)
        self.text_to_speech = TTSManager(synthesizer, audio_player)
