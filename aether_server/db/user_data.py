import os

import aiopg

__all__ = ["aiopg", "try_fetch_login_params_from_env"]

default_credentials = ("aether", "root", "secret", 5432)


def try_fetch_login_params_from_env():
    default_db, default_user, default_password, default_port = default_credentials

    db = os.getenv("DB_NAME", default_db)
    user = os.getenv("DB_USER", default_user)
    password = os.getenv("DB_PASSWORD", default_password)
    port = os.getenv("DB_PORT", default_port)

    return f"dbname={db} user={user} password={password} port={port}"
