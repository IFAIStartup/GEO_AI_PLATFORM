from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from geo_ai_backend.routers import routers
from geo_ai_backend.config import settings

__version__ = "0.1.0"


def create_app() -> Any:
    app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")

    secure = "s" if settings.HTTPS_ON else ""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"http{secure}://{settings.EXTERNAL_HOST}"] +
                      ([f"http{secure}://localhost:5173"] if not settings.ARABIC_STAND else []),
        # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    app.mount("/static", StaticFiles(directory="static"), name="static")

    routers(app=app)
    return app
