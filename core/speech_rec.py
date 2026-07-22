import speech_recognition as sr


class FasterWhisperSpeechRecognizer:
    def __init__(
            self, 
            *, 
            model: str = 'base',
            language: str = 'en',
            ambient_noice_adjustment: bool = True
        ) -> None:
        self.model_type = model
        self.language = language
        self.ambient_noice_adjustment = ambient_noice_adjustment

    def transcribe(self) -> str:
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()

        with self.mic as source:
            if self.ambient_noice_adjustment:
                self.recognizer.adjust_for_ambient_noise(source)

            audio_data = self.recognizer.listen(source)
            transcription = self.recognizer.recognize_faster_whisper(
                audio_data,
                model= self.model_type,
                language= 'en',
                vad_filter= True
            )

        return transcription
