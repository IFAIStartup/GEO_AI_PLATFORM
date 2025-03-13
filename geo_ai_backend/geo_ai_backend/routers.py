from fastapi import FastAPI

from geo_ai_backend.auth.router import router as auth_router
from geo_ai_backend.ml.router import router as ml_router
from geo_ai_backend.notification.router import router as notification_router
from geo_ai_backend.project.router import router as project_router
from geo_ai_backend.arcgis.router import router as arcgis_router
from geo_ai_backend.history.router import router as history_router


def routers(app: FastAPI) -> None:
    app.include_router(router=auth_router, prefix="/api")
    app.include_router(router=project_router, prefix="/api")
    app.include_router(router=ml_router, prefix="/api")
    app.include_router(router=notification_router, prefix="/api")
    app.include_router(router=arcgis_router, prefix="/api")
    app.include_router(router=history_router, prefix="/api")


