import asyncio
import os
import uuid
import requests
import logging
import urllib3

from config import SALUTE_CLIENT_ID
from .utils import convert_to_mono

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def get_access_token():
    """
    Получение Access Token для аутентификации в API SaluteSpeech.
    """
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_key = f"{SALUTE_CLIENT_ID}"
    headers = {
        "Authorization": f"Basic {auth_key}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "scope": "SALUTE_SPEECH_PERS"
    }
    response = requests.post(url,
                             headers=headers,
                             data=data,
                             verify=False,
                             )
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(
            f"Ошибка получения токена: {response.status_code} - "
            f"{response.text}")


async def upload_file_to_salute(file_path, client_id):
    """Загружает файл в SaluteSpeech и возвращает идентификатор файла"""
    url = "https://smartspeech.sber.ru/rest/v1/data:upload"
    headers = {
        "Authorization": f"Bearer {client_id}"
    }
    try:
        mono_file_path = file_path.replace(".mp3", "_mono.mp3")
        await convert_to_mono(file_path, mono_file_path)
        with open(mono_file_path, "rb") as audio_file:
            response = requests.post(url, headers=headers, data=audio_file, verify=False)
            response.raise_for_status()
            data = response.json()
            if "result" in data and "request_file_id" in data["result"]:
                request_file_id = data["result"]["request_file_id"]
                return request_file_id
            else:
                raise Exception("Не удалось загрузить файл. Нет идентификатора.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при загрузке файла в SaluteSpeech: {e}")
        return None
    finally:
        os.remove(file_path)


async def create_salute_task(request_file_id, client_id):
    """Создает задачу для распознавания аудио в SaluteSpeech и возвращает идентификатор задачи"""
    url = "https://smartspeech.sber.ru/rest/v1/speech:async_recognize"
    headers = {
        "Authorization": f"Bearer {client_id}",
        "Content-Type": "application/json"
    }
    body = {
        "options": {
            "language": "ru-RU",
            "audio_encoding": "MP3",
            # "sample_rate": 16000,
            "hypotheses_count": 1,
            "enable_profanity_filter": False,
            "max_speech_timeout": "20s",
            "channels_count": 1,
            "no_speech_timeout": "7s"
        },
        "request_file_id": request_file_id
    }
    try:
        response = requests.post(url, headers=headers, json=body, verify=False)
        response.raise_for_status()
        data = response.json()
        if "result" in data and "id" in data["result"]:
            task_id = data["result"]["id"]
            return task_id
        else:
            raise Exception("Не удалось создать задачу для распознавания.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при создании задачи для распознавания в SaluteSpeech: {e}")
        return None


async def get_task_status(task_id, client_id):
    """Проверяет статус задачи на распознавание аудио в SaluteSpeech"""
    url = f"https://smartspeech.sber.ru/rest/v1/task:get?id={task_id}"
    headers = {
        "Authorization": f"Bearer {client_id}"
    }
    try:
        while True:
            await asyncio.sleep(5)  # Проверяем каждые 5 секунд
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()
            if "result" in data and data["result"]["status"] == "DONE":
                return data["result"]
            elif "result" in data and data["result"]["status"] == "ERROR":
                logging.error(f"Ошибка при распознавании: {data['result']['error']}")
                return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при проверке статуса задачи SaluteSpeech: {e}")
        return None


async def download_result_from_salute(response_file_id, client_id):
    """
    Скачивание результата из SaluteSpeech по идентификатору файла.
    """
    url = f"https://smartspeech.sber.ru/rest/v1/data:download?response_file_id={response_file_id}"
    headers = {
        "Authorization": f"Bearer {client_id}"
    }
    try:
        # Отправка GET-запроса для скачивания результата
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Проверка на наличие HTTP-ошибок
        
        # Преобразование ответа в JSON
        data = response.json()

        # Логирование и возврат данных
        logging.info(f"Результаты скачивания из SaluteSpeech успешно получены.")
        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при скачивании результата из SaluteSpeech: {e}")
        return None

