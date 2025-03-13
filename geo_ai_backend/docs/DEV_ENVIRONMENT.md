### Before start dev

pip install pre-commit
pre-commit install --hook-type commit-msg


### Runing project
create `.env` file

start docker
```bash
docker compose -f 'docker-compose-local.yml' up
```

swagger url `http://127.0.0.1:8000/api/docs`


### Test users
```json
{   
    "email": "admin@mail.ru",
    "username": "admin",
    "password": "3tjq4UKTPwcXELuY",
    "role": "admin",
    "is_active": true,
}
{   
    "email": "user1@mail.ru",
    "username": "user1",
    "password": "2ceUoJpdIRtjGAbT",
    "role": "user",
    "is_active": true
}

{   
    "email": "user2@mail.ru",
    "username": "user2",
    "password": "Ne7AL4ZR2uP3q8sB",
    "role": "user",
    "is_active": false
}
```