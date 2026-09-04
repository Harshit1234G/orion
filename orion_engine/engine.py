from . import llm_api as llm
from . import memory_manager as memory
from . import tool_manager as tm
import skills
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
        self._agent_voice = agent_voice
        self._use_cuda_for_voice = use_cuda_for_voice
        self._recognition_model = recognition_model

        self.llm_client = llm.OpenAIClient()
        self.__init_tts()
        self.__init_stt()
        self.__init_tools()

        utils.logger.info(f'{LOGGING_NAME} Initialized Successfully.')

    def __init_tts(self) -> None:
        self.__synthesizer = voice.PiperSynthesizer(
            voice= self._agent_voice,
            use_cuda= self._use_cuda_for_voice
        )
        self.__audio_player = voice.SoundDevicePlayer(
            sample_rate= self.__synthesizer.frame_size
        )
        self.tts = voice.TTSManager(
            synthesizer= self.__synthesizer,
            audio_player= self.__audio_player
        )

    def __init_stt(self) -> None:
        self.__recorder = voice.SoundDeviceRecorder()
        self.__vad = voice.SileroVAD()
        self.__recognizer = voice.FasterWhisperRecognizer(
            model= self._recognition_model
        )
        self.stt = voice.STTManager(
            recorder= self.__recorder,
            vad= self.__vad,
            recognizer= self.__recognizer
        )

    def __init_tools(self) -> None:
        self.tool_manager = tm.ToolManager()
        
