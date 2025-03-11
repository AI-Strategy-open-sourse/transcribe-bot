import os
import uuid

from datetime import datetime
import aiofiles
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydub import AudioSegment
import speech_recognition as sr
from src.algo import algo
from src.audio import (process_audio_for_salute, process_audio_for_yandex,)
from config import YANDEX_SPEECHKIT_DIR, SALUTE_SPEECHKIT_DIR
from src.vosk import transcribe_vosk


def convert_file(file_name: str, save_audio_path: str):
    audio = AudioSegment.from_file(file_name)
    audio = audio.set_channels(1)  # Моно
    audio = audio.set_frame_rate(16000) 
    audio.export(save_audio_path, format="wav")



router = APIRouter()


@router.post("/yandex_speech_kit")
async def yandex_speech_kit_point(audio: UploadFile):
    try:
        # Сохраняем загруженный файл локально
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unique_id = str(uuid.uuid4())[:10]
        file_name = f"yandex_audio_{current_time}_processed_{unique_id}.mp3"
        local_file_path = os.path.join(YANDEX_SPEECHKIT_DIR, file_name)
        async with aiofiles.open(local_file_path, "wb") as buffer:
            content = await audio.read()
            await buffer.write(content)
        status, full_text, chunks = await process_audio_for_yandex(local_file_path, file_name)

        return JSONResponse(
            content={"message": {
                "status": status,
                "full_text": full_text,
                # "chunks": chunks,
            }},
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке файла: {str(e)}",
        )


@router.post("/salute_speech")
async def salute_speech_point(audio: UploadFile):
    try:
        # Сохраняем загруженный файл локально
        unique_id = str(uuid.uuid4())[:10]
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"salute_audio_{current_time}_processed_{unique_id}.mp3"
        local_file_path = os.path.join(SALUTE_SPEECHKIT_DIR, file_name)
        async with aiofiles.open(local_file_path, "wb") as buffer:
            content = await audio.read()
            await buffer.write(content)

        result = await process_audio_for_salute(local_file_path)

        return JSONResponse(
            content=result,
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке файла: {str(e)}",
        )

@router.post("/algo/vosk/small")
async def algo_speech_point(audio: UploadFile):
    try:
        # Сохраняем загруженный файл локально
        file_name = f"tmp/{uuid.uuid4()}.{audio.filename.split('.')[-1]}"
        async with aiofiles.open(file_name, "wb") as buffer:
            content = await audio.read()
            await buffer.write(content)

        path = algo(file_name, file_name)
        result = transcribe_vosk(path, "vosk-model-small-ru-0.22")
        return JSONResponse(
            content=result,
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке файла: {str(e)}",
        )
    
@router.post("/algo")
async def algo_speech_point(audio: UploadFile):
    try:
        # Сохраняем загруженный файл локально
        file_name = f"tmp/{uuid.uuid4()}.{audio.filename.split('.')[-1]}"
        async with aiofiles.open(file_name, "wb") as buffer:
            content = await audio.read()
            await buffer.write(content)

        path = algo(file_name, file_name)
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_name) as source:
            # Прослушиваем аудио и сохраняем его в переменную
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")  # Для русского языка
            # Выводим распознанный текст
            print("Распознанный текст: ", text)
            return JSONResponse(
                content=text,
                status_code=200,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке файла: {str(e)}",
        )
@router.post("/algo/only-transcrib")
async def algo_speech_point(audio: UploadFile):
        # Сохраняем загруженный файл локально
        file_name = f"tmp/{uuid.uuid4()}.{audio.filename.split('.')[-1]}"
        async with aiofiles.open(file_name, "wb") as buffer:
            content = await audio.read()
            await buffer.write(content)
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_name) as source:
            # Прослушиваем аудио и сохраняем его в переменную
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")  # Для русского языка
            # Выводим распознанный текст
            print("Распознанный текст: ", text)
            return JSONResponse(
                content=text,
                status_code=200,
            )
    # try:
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Ошибка при обработке файла: {str(e)}",
    #     )
    
@router.post("/algo/vosk/only-transcrib/small")
async def algo_speech_point(audio: UploadFile):
    # Сохраняем загруженный файл локально
    # try:
    file_name = f"tmp/{uuid.uuid4()}.{audio.filename.split('.')[-1]}"
    async with aiofiles.open(file_name, "wb") as buffer:
        content = await audio.read()
        await buffer.write(content)

    # Load MP3 
    # convert_file(file_name, file_name)

    result = transcribe_vosk(file_name, "vosk-model-small-ru-0.22")
    return JSONResponse(
        content=result,
        status_code=200,
    )
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Ошибка при обработке файла: {str(e)}",
    #     )
