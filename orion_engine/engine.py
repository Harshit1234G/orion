from . import llm_api as llm
from . import memory_manager as memory
from . import tool_manager as tools
from . import skill_manager as skills
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
        use_cuda_for_voice: bool = False
    ) -> None:
        self.llm_client = llm.OpenAIClient()
        self.tool_manager = tools.ToolManager()
        self.memory_manager = memory.MemoryManager()
        # self.skill_manager = skills.SkillManager()
        self.stt = voice.STTManager(
            model= recognition_model
        )
        self.tts = voice.TTSManager(
            voice= agent_voice, 
            use_cuda= use_cuda_for_voice
        )

        utils.logger.info(f'{LOGGING_NAME} Initialized Successfully.')
