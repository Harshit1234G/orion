from . import llm_api as llm
from . import memory_manager as memory
from . import tool_manager as tools
import voice_engine as voice
import prompts
import skills    # this import is required to load all skills automatically
import utils


LOGGING_NAME = '[OrionEngine]'


class OrionEngine:
    def __init__(
        self,
        agent_voice: str,
        *,
        recognition_model: str = 'base.en',
        use_cuda_for_voice: bool = False
    ) -> None:
        self.llm_client = llm.OpenAIClient()
        self.tool_manager = tools.ToolManager()
        self.memory_manager = memory.MemoryManager()
        self.stt = voice.STTManager(
            model= recognition_model
        )
        self.tts = voice.TTSManager(
            voice= agent_voice, 
            use_cuda= use_cuda_for_voice
        )

        utils.logger.info(f'{LOGGING_NAME} Initialized Successfully.')
