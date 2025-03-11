import os
import wave
import json
from vosk import Model, KaldiRecognizer

def transcribe_vosk(audio_path, model_path="vosk-model-ru-0.42"):
    """
    Транскрибирует аудио файл с использованием Vosk.
    
    :param audio_path: Путь к аудиофайлу (WAV формат, mono, 16kHz).
    :param model_path: Путь к распакованной модели Vosk.
    :return: Распознанный текст.
    """
    if not os.path.exists(model_path):
        print(f"Модель не найдена по пути: {model_path}")
        return ""
    
    wf = wave.open(audio_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000, 32000, 44100, 48000]:
        print("Аудио должно быть WAV моно 16kHz.")
        return ""
    
    model = Model(model_path)
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    
    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            results.append(result.get("text", ""))
    # Последний фрагмент
    final_result = json.loads(rec.FinalResult())
    results.append(final_result.get("text", ""))
    
    wf.close()
    return ' '.join(results)
