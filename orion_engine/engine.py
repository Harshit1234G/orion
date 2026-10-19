from enum import Enum, auto
from dataclasses import dataclass
from threading import Event, Lock
from concurrent.futures import ThreadPoolExecutor
import time

from . import llm_api as llm
from . import memory_manager as memory
from . import tool_manager as tools
import voice_engine as voice
import prompts
import skills    # this import is required to load all skills automatically
import utils


LOGGING_NAME = '[OrionEngine]'


# ----------------------
# Helper classes
# ----------------------
class OrionState(Enum):
    IDLE = auto()
    ACTIVE = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    STOPPING = auto()
    STOPPED = auto()


@dataclass(frozen= True)
class TranscriptDecision:
    intent: str
    confidence: float
    instruction: str


class TaskHandle:
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.cancel_event = Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    @property
    def cancelled(self) -> bool:
        return self.cancel_event.is_set()


# -----------------------
# Main engine class
# -----------------------
class OrionEngine:
    def __init__(
        self,
        agent_voice: str,
        *,
        recognition_model: str = 'base.en',
        use_cuda_for_voice: bool = False
    ) -> None:
        # initializing engine components
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

        # shutdown event 
        self._shutdown_event = Event()
        self._shutdown_lock = Lock()
        self._shutdown_complete = False

        # task executor
        self._task_executor = ThreadPoolExecutor(
            max_workers= 1,
            thread_name_prefix= 'OrionTask'
        )
        self._active_task: TaskHandle | None = None
        self._next_task_id = 0

        self.state = OrionState.IDLE
        self._last_activity = time.monotonic()

        utils.logger.info(f'{LOGGING_NAME} Initialized Successfully.')

    def _set_state(self, state: OrionState) -> None:
        self.state = state
        utils.logger.debug(f'{LOGGING_NAME} State changed to {state.name}')
    
    def _handle_transcript(self, transcript: str) -> None:
        decision = self.llm_client.decide(
            input= transcript,
            questions= prompts.INTENT_DETECTION
        )

        decision = TranscriptDecision(
            intent= decision.answers[0].choice,
            confidence= decision.answers[0].confidence,
            instruction= transcript
        )

        self._route_decision(decision)

    def _route_decision(self, decision: TranscriptDecision) -> None:
        match decision.intent:
            case 'wakeword':
                ...    # it will mainly be UI related, so nothing happens right now

            case 'interrupt':
                ...

            case 'cancel_task':
                ...

            case 'instruction':
                ...

            case 'gibberish':
                ...

    def _shutdown(self) -> None:
        with self._shutdown_lock:
            if self._shutdown_complete:
                return

            self._shutdown_complete = True
            self._shutdown_event.set()
            self._set_state(OrionState.STOPPING)

        self.tts.interrupt()

        for name, component in (
            ('STT', self.stt),
            ('TTS', self.tts), 
            ('Memory', self.memory_manager)
        ):
            try:
                component.shutdown()

            except Exception as e:
                utils.logger.exception(f'{LOGGING_NAME} Failed to shut down {name}: {e}')

        self._set_state(OrionState.STOPPED)

    def request_shutdown(self) -> None:
        self._shutdown_event.set()

    def main_loop(self) -> None:
        self.stt.start_listening()
        self.memory_manager.create_tables()    # only creates tables is doesn't exist

        try:
            while not self._shutdown_event.is_set():
                if not self.stt.is_listening:
                    utils.logger.warning(f'{LOGGING_NAME} STT stoped unexpectedly.')
                    break

                transcript = self.stt.get_transcript(timeout= 0.25)

                if transcript is None or not transcript:
                    continue

                self._last_activity = time.monotonic()
                self._handle_transcript(transcript)

        except KeyboardInterrupt:
            self.request_shutdown()

        except Exception as e:
            utils.logger.exception(f'{LOGGING_NAME} Unhandled engine error')
            raise utils.OrionEngineException() from e

        finally:
            self._shutdown()
