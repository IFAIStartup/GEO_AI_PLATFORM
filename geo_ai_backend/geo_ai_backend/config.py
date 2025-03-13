import os
from dotenv import load_dotenv
from pydantic import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings(BaseSettings):
    """Global config."""

    # RUN
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8001))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "debug")
    EXTERNAL_HOST: str = os.getenv("EXTERNAL_HOST")
    RELOAD: bool = bool(os.getenv("RELOAD", True))
    DEBUG: bool = bool(os.getenv("DEBUG", True))
    ARABIC_STAND: bool = bool(os.getenv("RELOAD", False))
    HTTPS_ON: bool = bool(os.getenv("HTTPS_ON", True))

    # Email
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD")
    MAIL_FROM: str = os.getenv("MAIL_FROM")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 0))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME")

    # Token
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 60))
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")

    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # NEXTCLOUD
    URL_NEXTCLOUD: str = os.getenv("URL_NEXTCLOUD")
    PORT_NEXTCLOUD: int = int(os.getenv("PORT_NEXTCLOUD", 49080))
    LOGIN_NEXTCLOUD: str = os.getenv("LOGIN_NEXTCLOUD")
    PASSWORD_NEXTCLOUD: str = os.getenv("PASSWORD_NEXTCLOUD")
    URL_DOWNLOAD_NEXTCLOUD: str = os.getenv("URL_DOWNLOAD_NEXTCLOUD")

    # REDIS
    BROKER_URL: str = os.getenv("BROKER_URL")
    BROKER_PORT: str = os.getenv("BROKER_PORT")
    RESULT_BACKEND: str = os.getenv("RESULT_BACKEND")
    RESULT_BACKEND_PORT: str = os.getenv("RESULT_BACKEND_PORT")
    RESULT_EXTENDED: bool = bool(os.getenv("RESULT_EXTENDED"))

    # WORKER
    WORKER_HOST: str = os.getenv("API_HOST")
    WORKER_PORT: str = os.getenv("WORKER_PORT")

    # TRITON
    TRITON_HOST: str = os.getenv("API_HOST")
    TRITON_PORT: str = os.getenv("TRITON_PORT")

    # AD
    LDAP_ON: bool = bool(os.getenv("LDAP_ON"))
    LDAP_DOMAIN: str = os.getenv("LDAP_DOMAIN")
    LDAP_SERVER: str = os.getenv("LDAP_SERVER")

    # ARCGIS
    ARCGIS_URL: str = os.getenv("ARCGIS_URL")
    ARCGIS_PATH: str = os.getenv("ARCGIS_PATH")
    ARCGIS_LOGIN: str = os.getenv("ARCGIS_LOGIN")
    ARCGIS_PASSWORD: str = os.getenv("ARCGIS_LOGIN")
    ARCGIS_VERIFY_CERT: bool = bool(os.getenv("ARCGIS_VERIFY_CERT"))
    ARCGIS_OVERWRITE: bool = bool(os.getenv("ARCGIS_OVERWRITE"))
    CLIENT_HOST: str = os.getenv("CLIENT_HOST")
    ACCESS_ARCGIS_TOKEN_EXPIRE_MINUTES: str = os.getenv("ACCESS_ARCGIS_TOKEN_EXPIRE_MINUTES")

    # MLFLOW
    MLFLOW_PROD: bool = bool(os.getenv("MLFLOW_PROD"))
    MLFLOW_PROD_URL: str = os.getenv("MLFLOW_PROD_URL")
    MLFLOW_ON: bool = bool(os.getenv("MLFLOW_ON"))
    URL_MLFLOW: str = os.getenv("URL_MLFLOW")
    PROT_MLFLOW: int = int(os.getenv("PROT_MLFLOW"))
    LOGIN_MLFLOW: str = os.getenv("LOGIN_MLFLOW")
    PASSWORD_MLFLOW: str = os.getenv("PASSWORD_MLFLOW")

    # DB ENGINE
    POOL_SIZE_ENGINE: int = int(os.getenv("POOL_SIZE_ENGINE"))

    # ML SERVER
    ML_SERVER_URL: str = os.getenv("ML_SERVER_URL")
    ML_SERVER_PORT: str = os.getenv("ML_SERVER_PORT")
    ML_MLFLOW_PORT: str = os.getenv("ML_MLFLOW_PORT")

    # BACKEND
    NOTIFICATION_ON: bool = bool(os.getenv("NOTIFICATION_ON", False))

settings = Settings()
