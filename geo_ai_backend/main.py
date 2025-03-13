import asyncio
import logging
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends  # ✅ Added Depends
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every

from sqlalchemy import event
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from geo_ai_backend import create_app
from geo_ai_backend.config import settings
from geo_ai_backend.database import get_db, get_db_iter
from geo_ai_backend.notification.models import Notification
from geo_ai_backend.notification.service import get_new_notification_service
from geo_ai_backend.auth.service import create_default_ml_user_service
from geo_ai_backend.ml.service import unload_unused_ml_models_service

logger = logging.getLogger(__name__)

app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("wss://0.0.0.0:8090/ws");  
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.on_event("startup")
@repeat_every(seconds=60 * 60)  # 1 hour
def unload_unused_ml_models() -> None:
    db = get_db_iter()
    unload_unused_ml_models_service(db=db)
    logger.info("Clear unused ml model")


@app.on_event("startup")
def create_default_mlflow_user():
    if settings.MLFLOW_ON:
        create_default_ml_user_service()


@app.get("/")
async def get() -> HTMLResponse:
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)) -> None:
    flag = asyncio.Event()

    @event.listens_for(Notification, "after_insert")
    def notification_stream(*args, **kwargs) -> Any:
        flag.set()

    await websocket.accept()
    while True:
        try:
            await flag.wait()
            notification = get_new_notification_service(db=db)
            await websocket.send_json(jsonable_encoder(notification.dict()))
            flag.clear()
        except WebSocketDisconnect:
            return None


if __name__ == "__main__":
    uvicorn_params = {
        "app": "main:app",
        "host": settings.HOST,
        "port": settings.PORT,
        "log_level": settings.LOG_LEVEL,
        "reload": settings.RELOAD,
    }

    # ✅ Added: Run with SSL if HTTPS is enabled
    if settings.HTTPS_ON:
        uvicorn_params["ssl_keyfile"] = "/etc/nginx/key.pem"
        uvicorn_params["ssl_certfile"] = "/etc/nginx/certificate.pem"

    uvicorn.run(**uvicorn_params)