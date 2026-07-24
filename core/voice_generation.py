from queue import Queue
from threading import Thread
from pathlib import Path
from dataclasses import dataclass
from piper import PiperVoice
import sounddevice as sd


class PiperVoiceThreadedTTS:
    def __init__(
            self, 
            voice: str, 
            *, 
            voices_dir: str = 'voices', 
            use_cuda: bool = False,
            queue_size: int = 0
        ) -> None:
        voice_path = Path(voices_dir) / f'{voice}.onnx'
        self.voice = PiperVoice.load(voice_path, use_cuda= use_cuda)
        self.queue = Queue(maxsize= queue_size)
        self._STOP = object()
        self.stop_requested = False

        self.worker = Thread(target= self.__tts_worker)
        self.worker.start()


    def __tts_worker(self) -> None:
        stream = sd.OutputStream(
            samplerate= self.voice.config.sample_rate,
            channels= 1,
            dtype= 'int16',
            blocksize= 0,
            latency= 'low'
        )
        stream.start()
    
        while True:
            try:
                request = self.queue.get()
        
                if request is self._STOP:
                    break

                if self.stop_requested and request.interrupt:
                    break
        
                for audio_chunk in self.voice.synthesize(request.text):
                    stream.write(audio_chunk.audio_int16_array)

            except Exception as e:
                print(e)
    
        stream.stop()
        stream.close()

    # wrapper / helper function for simple calling of tts
    def say(
            self, 
            text: str, 
            *,
            interrupt: bool = True
        ) -> None:
        request = SpeechRequest(text, interrupt)
        self.queue.put(request)

    def stop(self) -> None:
        self.queue.put(self._STOP)
        self.worker.join()


@dataclass
class SpeechRequest:
    text: str
    interrupt: bool
        