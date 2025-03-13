from geo_ai_backend.config import settings


secure = "s" if settings.HTTPS_ON else ""
BACKEND_HOST = f"http{secure}://{settings.WORKER_HOST}:{settings.WORKER_PORT}/"
API_PATH = "api/notification/create-notification"
