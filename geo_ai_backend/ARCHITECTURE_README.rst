1. Project Structure.

GEO_AI_BACKEND
├── alembic/
├── geo_ai_backend
│   ├── auth
│   │   ├── router.py # is a core of each module with all the endpoints
│   │   ├── schemas.py  # pydantic models
│   │   ├── models.py  # db models
│   │   ├── dependencies.py
│   │   ├── config.py  # local configs
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── service.py
│   │   └── utils.py
│   └── posts
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── service.py
│   │   └── utils.py
│   ├── config.py  # global configs
│   ├── models.py  # global models
│   ├── exceptions.py  # global exceptions
│   ├── pagination.py  # global module e.g. pagination
│   └── database.py  # db connection related stuff
├── tests
│   ├── auth
│   └── posts
├── .venv
├── .gitignore
├── main.py
├── Dockerfile
├── logging.ini
└── alembic.ini

1. Store all domain directories inside src folder
    * geo_ai_backend/ - highest level of an app, contains common models, configs, and constants, etc.
    * geo_ai_backend/main.py - root of the project, which inits the FastAPI app
2. Each package has its own router, schemas, models, etc.
    * router.py - is a core of each module with all the endpoints
    * schemas.py - for pydantic models
    * models.py - for db models
    * service.py - module specific business logic
    * dependencies.py - router dependencies
    * constants.py - module specific constants and error codes
    * config.py - e.g. env vars
    * utils.py - non-business logic functions, e.g. response normalization, data enrichment, etc.
    * exceptions - module specific exceptions, e.g. PostNotFound, InvalidUserData

[Processes and agreements in development](/docs/DEV_PROCESS.md)
