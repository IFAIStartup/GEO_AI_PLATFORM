import pytest


def create_admin(client):
    params = {
        "email": "admin@example.com",
        "role": "admin",
    }
    return client.post("/api/auth/create-user", json=params)


def login(client, login_params):
    response = client.post("/api/auth/login", json=login_params)
    return response


@pytest.mark.parametrize(
    "params, expected_status, expected_response",
    (
        (
            {
                "email": "user@example.com",
                "role": "user",
            },
            200,
            {
                "email": "user@example.com",
                "username": "user",
                "role": "user",
                "external_user": True,
            },
        ),
        (
            {
                "email": "user1@example.com",
                "username": "username",
                "role": "user",
            },
            200,
            {
                "email": "user1@example.com",
                "username": "username",
                "role": "user",
            },
        ),
        (
            {
                "email": "user@example.com",
                "role": "user",
            },
            400,
            {"detail": "Email already registered"},
        ),
    ),
)
def test_create_user(client, params, expected_status, expected_response):
    login_params = {"email": "admin@mail.ru", "password": "3tjq4UKTPwcXELuY"}
    response_login = client.post("/api/auth/login", json=login_params)
    assert response_login.status_code == 200
    headers = {"Authorization": f"Bearer {response_login.json()['access_token']}"}
    response_created_user = client.post(
        "/api/auth/create-user", json=params, headers=headers
    )
    assert response_created_user.status_code == expected_status
    user = {i: response_created_user.json()[i] for i in expected_response.keys()}
    assert user == expected_response


@pytest.mark.parametrize(
    "user_params, expected_user",
    (
        (
            {
                "email": "admin@mail.ru",
                "password": "3tjq4UKTPwcXELuY",
            },
            {
                "id": 1,
                "email": "admin@mail.ru",
                "username": "admin",
                "role": "admin",
                "created_at": "2023-05-31T15:15:12.341000Z",
                "is_active": True,
                "external_user": True,
            },
        ),
    ),
)
def test_login_user(client, user_params, expected_user):
    login_params = {"email": user_params["email"], "password": user_params["password"]}
    response_login = client.post("/api/auth/login", json=login_params)
    assert response_login.status_code == 200
    assert response_login.json()["access_token"]
    assert response_login.json()["user"] == expected_user


@pytest.mark.parametrize(
    "user_params",
    (
        (
            {
                "email": "admin@mail.ru",
                "password": "3tjq4UKTPwcXELuY",
            }
        ),
    ),
)
def test_logout_user(client, user_params):
    login_params = {"email": user_params["email"], "password": user_params["password"]}
    response_login = client.post("/api/auth/login", json=login_params)
    assert response_login.status_code == 200
    headers = {"Authorization": f"Bearer {response_login.json()['access_token']}"}
    response_logout = client.get("/api/auth/logout", headers=headers)
    assert response_logout.status_code == 200


@pytest.mark.parametrize(
    "user_id, expected_status, expected_response",
    (
        (
            2,
            200,
            {
                "status": "ok",
                "user": {
                    "id": 2,
                    "email": "user@example.com",
                    "role": "user",
                    "is_active": False,
                    "external_user": True,
                },
            },
        ),
    ),
)
def test_delete_user(client, user_id, expected_status, expected_response):
    login_params = {"email": "admin@mail.ru", "password": "3tjq4UKTPwcXELuY"}
    response_login = client.post("/api/auth/login", json=login_params)
    assert response_login.status_code == 200
    headers = {"Authorization": f"Bearer {response_login.json()['access_token']}"}

    response_deleted = client.post(
        f"/api/auth/delete-user?id={user_id}", headers=headers
    )
    assert response_deleted.status_code == expected_status
    user_deleted = response_deleted.json()
    assert user_deleted["status"] == expected_response["status"]
    user = {i: user_deleted["user"][i] for i in expected_response["user"].keys()}
    assert user == expected_response["user"]
