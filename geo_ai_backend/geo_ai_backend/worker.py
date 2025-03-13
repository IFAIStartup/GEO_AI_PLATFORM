from celery import Celery

from geo_ai_backend.config import settings

celery = Celery(
    __name__,
    backend=f"{settings.RESULT_BACKEND}:{settings.RESULT_BACKEND_PORT}",
    broker=f"{settings.BROKER_URL}:{settings.BROKER_PORT}",
    result_extended=settings.RESULT_EXTENDED
)
