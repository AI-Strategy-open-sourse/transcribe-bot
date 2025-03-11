import logging

from pydub import AudioSegment

from .utils import (
    remove_background_audio,
    apply_vad,
    filter_hallucinations,
)
from src.salutespeech_transcribe import (
    upload_file_to_salute,
    create_salute_task,
    get_task_status,
    get_access_token,
    download_result_from_salute,
)
from src.yandex_transcribe import upload_file_to_s3


async def process_audio_for_yandex(audio_path: AudioSegment, file_name) -> str:
    try:
        # Применяем VaD для удаления участков тишины
        vad_processed_path = await apply_vad(audio_path, audio_path.replace(".mp3", "_vad.mp3"))
        if not vad_processed_path:
            raise Exception("Ошибка при применении VaD")

        # Определяем путь на S3
        s3_file_name = f"yandex/{file_name}"

        # Загружаем файл в Yandex Cloud
        status, full_text, chunks = await upload_file_to_s3(
            local_file_path=vad_processed_path,
            s3_file_name=s3_file_name,
        )
        full_text = await filter_hallucinations(full_text)
        return status, full_text, chunks

    except Exception as e:
        logging.error(f"Ошибка при обработке файла для Yandex Speechkit: {str(e)}")
        raise e


async def process_audio_for_salute(audio_path: AudioSegment) -> dict:
    try:
        # Загрузка файла в SaluteSpeech
        access_token = await get_access_token()
        request_file_id = await upload_file_to_salute(audio_path, access_token)
        if not request_file_id:
            raise Exception("Ошибка при загрузке файла в SaluteSpeech")

        # Создание задачи для транскрибации
        task_id = await create_salute_task(request_file_id, access_token)
        if not task_id:
            raise Exception(
                "Ошибка при создании задачи для транскрибации в SaluteSpeech"
            )

        # Проверка статуса задачи
        task_status = await get_task_status(task_id, access_token)
        if not task_status:
            raise Exception("Ошибка при распознавании аудио в SaluteSpeech")
        response_file_id = task_status.get("response_file_id")

        result = await download_result_from_salute(response_file_id, access_token)
        # Обработка текста для удаления галлюцинаций
        if isinstance(result, list) and len(result) > 0:
            transcribed_texts = []
            for segment in result:
                # Проверяем наличие ключа "results" в каждом сегменте
                if "results" in segment:
                    for hypothesis in segment["results"]:
                        transcribed_text = hypothesis.get("normalized_text", "")
                        if transcribed_text:
                            transcribed_texts.append(transcribed_text)

            # Объединяем все тексты в один
            full_transcribed_text = " ".join(transcribed_texts)
        else:
            raise Exception("Некорректный формат ответа из SaluteSpeech")
        filtered_text = await filter_hallucinations(full_transcribed_text)
        # filtered_text += "\n\n"
        return {
            "message": "Аудиофайл успешно распознан",
            "task_result": filtered_text,
        }

    except Exception as e:
        logging.error(f"Ошибка при обработке файла для Salute Speech: {str(e)}")
        raise e
