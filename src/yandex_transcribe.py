import os
import asyncio
import requests
import logging
import boto3.session

from pydub import AudioSegment

from config import (
    YANDEX_CLOUD,
    BUCKET_NAME,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    YANDEX_S3_ENDPOINT_URL,
)
from .utils import convert_to_mono

from botocore.exceptions import NoCredentialsError


session = boto3.session.Session()

# Инициализация клиента S3 для Яндекс Облака
s3_client = session.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=YANDEX_S3_ENDPOINT_URL,
    region_name="ru-central1",
)



async def upload_file_to_s3(local_file_path, s3_file_name):
    """Загружает файл в S3 хранилище Яндекс Облака"""
    try:
        mono_file_path = local_file_path.replace(".mp3", "_mono.mp3")
        await convert_to_mono(local_file_path, mono_file_path)
        s3_client.upload_file(
            mono_file_path,
            BUCKET_NAME,
            s3_file_name,
        )
        # s3_url = f"https://{BUCKET_NAME}.storage.yandexcloud.net/{s3_file_name}"
        status, full_text, chunks = await transcribe_audio(object_name=s3_file_name)
        return status, full_text, chunks
    except FileNotFoundError:
        raise Exception("Файл не найден")
    except NoCredentialsError:
        raise Exception("Недоступны учетные данные для доступа к S3")
    finally:
        os.remove(local_file_path)


async def transcribe_audio(object_name: str) -> tuple[str, str, dict]:
    key = YANDEX_CLOUD
    bucket_name = BUCKET_NAME

    filelink = f"https://{bucket_name}.storage.yandexcloud.net/{object_name}"

    POST = (
        "https://transcribe.api.cloud.yandex.net/speech/" "stt/v2/longRunningRecognize"
    )

    body = {
        "config": {
            "specification": {
                "languageCode": "ru-RU",
                "audioEncoding": "MP3",
                "literature_text": True,
            }
        },
        "audio": {"uri": filelink},
    }

    header = {"Authorization": f"Api-Key {key}"}

    try:
        response = requests.post(POST, headers=header, json=body)
        response.raise_for_status()  # Проверяем, нет ли ошибок на уровне HTTP
        data = response.json()

        if "id" not in data:
            error_message = data.get("message", "Unknown error")
            logging.error(f"Ошибка при транскрибации: {error_message}")
            return "error", "", {}, error_message

        operation_id = data.get("id")
        logging.info(f"Операция транскрибации начата. " f"ID операции: {operation_id}")

        # Проверка статуса выполнения транскрибации
        GET = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"
        while True:
            await asyncio.sleep(5)
            status_response = requests.get(GET, headers=header)
            status_response.raise_for_status()  # Проверяем HTTP ошибки
            req = status_response.json()

            if req.get("done"):
                if "error" in req:
                    error_message = req["error"].get("message", "Unknown error")
                    logging.error(
                        f"Ошибка при выполнении операции "
                        f"транскрибации: {error_message}"
                    )
                    return "error", "", {}, error_message

                break

        full_text = " ".join(
            [chunk["alternatives"][0]["text"] for chunk in req["response"]["chunks"]]
        )
        status = "done"
        chunks = req["response"]["chunks"]

        return status, full_text, chunks

    except requests.exceptions.HTTPError as http_err:
        # Логирование ошибки HTTP и возврат сообщения об ошибке
        error_message = response.json().get("message", str(http_err))
        logging.error(f"HTTP ошибка при транскрибации: {error_message}")
        return "error", "", {}, error_message
    except Exception as e:
        logging.error(f"Ошибка при транскрибации файла {filelink}: {e}")
        return "error", "", {}, str(e)
