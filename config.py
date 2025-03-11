import os

from dotenv import load_dotenv

load_dotenv(override=True)

API_TOKEN = os.getenv("API_TOKEN")

YANDEX_CLOUD = os.getenv("YANDEX_CLOUD")
BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
YANDEX_S3_ENDPOINT_URL = os.getenv("YANDEX_S3_ENDPOINT_URL")

SALUTE_CLIENT_SECRET = os.getenv("SALUTE_CLIENT_SECRET")
SALUTE_CLIENT_ID = os.getenv("SALUTE_CLIENT_ID")

ELEVENLABS_KEY = os.getenv("ELEVENLABS_KEY")

current_dir = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS = os.path.join(current_dir, "downloads")

YANDEX_SPEECHKIT_DIR = os.path.join(DOWNLOADS, "yandex_speechkit")
SALUTE_SPEECHKIT_DIR = os.path.join(DOWNLOADS, "salute_speechkit")

if not os.path.exists(YANDEX_SPEECHKIT_DIR):
    os.makedirs(YANDEX_SPEECHKIT_DIR)

if not os.path.exists(SALUTE_SPEECHKIT_DIR):
    os.makedirs(SALUTE_SPEECHKIT_DIR)
