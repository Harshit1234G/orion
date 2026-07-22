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

        Thread(target= self.__tts_worker, daemon= True).start()


    def __tts_worker(self) -> None:
        stream = sd.OutputStream(
            samplerate= self.voice.config.sample_rate,
            channels= 1,
            dtype= 'int16'
        )
    
        stream.start()
    
        while True:
            text = self.queue.get()
    
            if text is None:
                break
    
            for audio_chunk in self.voice.synthesize(text):
                stream.write(audio_chunk.audio_int16_array)
    
        stream.stop()
        stream.close()


    def say(self, text: str) -> None:
        self.queue.put(text)
