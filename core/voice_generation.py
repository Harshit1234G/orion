from queue import Queue
from threading import Thread
from pathlib import Path
from piper import PiperVoice
import sounddevice as sd


class PiperVoiceThreadedTTS:
    def __init__(
            self, 
            voice: str, 
            *, 
            voices_dir: str = 'voices', 
            use_cuda: bool = False
        ) -> None:
        voice_path = Path(voices_dir) / f'{voice}.onnx'
        self.voice = PiperVoice.load(voice_path, use_cuda= use_cuda)
        self.queue = Queue()

        # daemon is for low priority thread
        self.worker = Thread(target= self.__tts_worker, daemon= True)
        self.worker.start()

        # sentinal
        self._STOP = object()

    def __tts_worker(self) -> None:
        stream = sd.OutputStream(
            samplerate= self.voice.config.sample_rate,
            channels= 1,
            dtype= 'int16'
        )
        stream.start()
    
        while True:
            try:
                text = self.queue.get()
        
                if text is self._STOP:
                    break
        
                for audio_chunk in self.voice.synthesize(text):
                    stream.write(audio_chunk.audio_int16_array)

            except Exception as e:
                print(e)
    
        stream.stop()
        stream.close()

    # wrapper / helper function for simple calling of tts
    def say(self, text: str) -> None:
        self.queue.put(text)

    def stop(self) -> None:
        self.queue.put(self._STOP)
        self.worker.join()