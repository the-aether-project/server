import os
import pathlib
from collections import namedtuple

import aiohttp.web as web
import aiopg

POOL_APPKEY = web.AppKey("database_pool", aiopg.Pool)

credentials = namedtuple(
    "credentials",
    ("db", "user", "password", "host", "port"),
    defaults=("aether", "root", "secret", "127.0.0.1", 5432),
)
default_credentials = credentials()
schema_path = (pathlib.Path(__file__) / "../schema.sql").resolve()


def try_fetch_login_params_from_env(default_credentials=default_credentials):
    (
        default_db,
        default_user,
        default_password,
        default_host,
        default_port,
    ) = default_credentials

    db = os.getenv("DB_NAME", default_db)
    user = os.getenv("DB_USER", default_user)
    password = os.getenv("DB_PASSWORD", default_password)
    host = os.getenv("DB_HOST", default_host)
    port = os.getenv("DB_PORT", default_port)

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


__all__ = ["try_fetch_login_params_from_env", "schema_path", "POOL_APPKEY"]
