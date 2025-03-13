import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from geo_ai_backend import create_app
from geo_ai_backend.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = TestingSessionLocal()


def create_admin(db):
    db.execute(
        text(
            """
                INSERT 
                    INTO users (email, username, created_at, password, role, is_active, external_user) 
                    VALUES (
                        'admin@mail.ru', 
                        'admin',
                        '2023-05-31 15:15:12.341', 
                        '$2b$12$VaUQdeCnJbfiEr9MvwgLbu/doApKZW2taQ0oxx7d5D7nUyl643LEK', 
                        'admin', 
                        true,
                        true
                    );
            """
        )
    )
    db.commit()
    db.close()


create_admin(db=db)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
