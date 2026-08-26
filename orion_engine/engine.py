from . import llm_api as llm
from . import multi_step_planner as planner
from . import safety_validator as safety
import memory_manager as memory
import voice_engine as voice
import prompts
import utils


LOGGING_NAME = '[OrionEngine]'


class OrionEngine:
    def __init__(
        self,
        agent_voice: str,
        *,
        recognition_model: str = 'base.en',
        use_cuda_for_voice: bool = False,
    ) -> None:
        self.agent_voice = agent_voice
        self.use_cuda_for_voice = use_cuda_for_voice
        self.recognition_model = recognition_model

        self.__init_llm()
        self.__init_tts()
        self.__init_stt()

        utils.logger.info(f'{LOGGING_NAME} Initialized Successfully.')

    def __init_llm(self) -> None:
        self.llm_client = llm.OpenAIClient()
        self.capability_registery = llm.CapabilityRegistery()

    def __init_tts(self) -> None:
        self.synthesizer = voice.PiperSynthesizer(
            voice= self.agent_voice,
            use_cuda= self.use_cuda_for_voice
        )
        self.audio_player = voice.SoundDevicePlayer(
            sample_rate= self.synthesizer.frame_size
        )
        self.tts = voice.TTSManager(
            synthesizer= self.synthesizer,
            audio_player= self.audio_player
        )

    def __init_stt(self) -> None:
        self.recorder = voice.SoundDeviceRecorder()
        self.vad = voice.SileroVAD()
        self.recognizer = voice.FasterWhisperRecognizer(
            model= self.recognition_model
        )
        self.stt = voice.STTManager(
            recorder= self.recorder,
            vad= self.vad,
            recognizer= self.recognizer
        )
