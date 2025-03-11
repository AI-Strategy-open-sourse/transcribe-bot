import uvicorn
from fastapi import FastAPI
from routers import transcribe_router

# Создаем приложение FastAPI
app = FastAPI(title="Transcribe audio")

# Подключаем маршруты
app.include_router(transcribe_router.router)

# Точка входа для запуска сервера
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)