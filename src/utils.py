import logging
import torch
import re
import soundfile as sf

from pydub import AudioSegment

from elevenlabs import ElevenLabs

from config import ELEVENLABS_KEY
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

client = ElevenLabs(api_key=ELEVENLABS_KEY)


# AudioSegment.converter = which("/usr/bin/ffmpeg")
# vad_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=True)
vad_model = load_silero_vad()

# get_speech_timestamps = utils[0]

STOP_WORDS = [
    "эмм", "эээ", "типа", "ну это", "мм", "вроде как", "короче", 
    "это самое", "в общем", "как его там", "что-то типа"
]


async def convert_to_mono(audio_path: str, output_path: str):
    audio = AudioSegment.from_file(audio_path)
    mono_audio = audio.set_channels(1)
    mono_audio.export(output_path, format="mp3")


async def remove_background_audio(audio_path):
    try:
        with open(audio_path, "rb") as audio_file:
        # Perform audio isolation
            isolated_audio_iterator = client.audio_isolation.audio_isolation(audio=audio_file)

            # Save the isolated audio to a new file
            audio_file_path = audio_path.replace(".mp3", "_cleaned_file.mp3")
            output_file_path = f"{audio_file_path}"
            with open(output_file_path, "wb") as output_file:
                for chunk in isolated_audio_iterator:
                    output_file.write(chunk)


        print(f"Isolated audio saved to {output_file_path}")
        return output_file_path
    except Exception as e:
        logging.error(
            f"Произошла ошибка при удалении шумов в elevenlabs\n{e}"
        )


# Стоп-слова или стоп-фразы, которые могут быть "галлюцинациями"

async def filter_hallucinations(transcribed_text):
    # Убираем все слова из списка STOP_WORDS
    for word in STOP_WORDS:
        transcribed_text = re.sub(rf'\b{word}\b', '', transcribed_text, flags=re.IGNORECASE)
    
    # Убираем лишние пробелы
    transcribed_text = re.sub(r'\s+', ' ', transcribed_text).strip()
    
    return transcribed_text


# Функция для применения VaD к аудиофайлу
async def apply_vad(audio_file_path, output_file_path):
    try:
        # Сначала конвертируем аудио в моно, если оно стерео
        audio = AudioSegment.from_file(audio_file_path)
        original_frame_rate = audio.frame_rate  # Сохраняем исходную частоту дискретизации
        original_channels = audio.channels  # Сохраняем исходное количество каналов

        # Преобразование аудио в моно, если в нем более одного канала
        if audio.channels > 1:
            logging.info(f"Конвертация файла {audio_file_path} в моно...")
            audio = audio.set_channels(1)

        # Преобразование частоты дискретизации в 16000 Гц, если это необходимо
        if audio.frame_rate != 16000:
            logging.info(f"Изменение частоты дискретизации файла {audio_file_path} на 16000 Гц...")
            audio = audio.set_frame_rate(16000)

        # Сохраняем преобразованное аудио во временный файл в формате WAV
        temp_mono_path = f"{audio_file_path}_mono_16kHz.wav"
        audio.export(temp_mono_path, format="wav")
        audio_file_path = temp_mono_path

        # Используем soundfile для считывания аудиофайла
        wav, sr = sf.read(audio_file_path)

        # Проверяем количество каналов и конвертируем в одномерный массив, если требуется
        if wav.ndim > 1:
            logging.info(f"Конвертация многоканального аудио в одномерный массив для файла {audio_file_path}...")
            wav = wav.mean(axis=1)  # Среднее значение по каналам для получения моно

        # Определяем таймстампы с участками речи с помощью модели VAD
        speech_timestamps = get_speech_timestamps(
            wav,
            vad_model,
            return_seconds=True,  # Return speech timestamps in seconds (default is samples)
        )

        # Проверяем, были ли найдены речевые сегменты
        if not speech_timestamps:
            logging.warning(f"No speech segments found in the file {audio_file_path}")
            return None

        # Загружаем аудиофайл для обрезки с помощью Pydub
        audio = AudioSegment.from_file(audio_file_path)

        # Собираем аудио участки, где есть речь
        speech_audio = AudioSegment.empty()
        for timestamp in speech_timestamps:
            start = timestamp['start'] / sr * 1000  # переводим в миллисекунды
            end = timestamp['end'] / sr * 1000  # переводим в миллисекунды
            speech_audio += audio[start:end]

        # Возвращаем частоту дискретизации и количество каналов к исходным значениям
        if original_channels > 1:
            logging.info(f"Возвращаем количество каналов к исходному значению {original_channels} для файла {output_file_path}")
            speech_audio = speech_audio.set_channels(original_channels)

        if original_frame_rate != 16000:
            logging.info(f"Возвращаем частоту дискретизации к исходному значению {original_frame_rate} Гц для файла {output_file_path}")
            speech_audio = speech_audio.set_frame_rate(original_frame_rate)

        # Сохраняем предобработанный файл
        speech_audio.export(output_file_path, format="mp3")

        return output_file_path

    except Exception as e:
        logging.error(f"Произошла ошибка при применении VAD к файлу {audio_file_path}\n{e}")
        return None
