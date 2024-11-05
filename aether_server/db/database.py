import os

import aiopg

default_credentials = ("aether", "root", "secret", "postgres", 5432)


async def setup_database():
    default_db, default_user, default_password, default_host, default_port = (
        default_credentials
    )

    dsn = f"user={default_user} password={default_password} host={default_host} port={default_port}"

    # Establish connection and execute to test if db exist or not
    async with aiopg.connect(dsn=dsn) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                (f"SELECT 1 FROM pg_database WHERE datname = '{default_db}';")
            )
            exist = await cur.fetchone()

            if exist[0] != 1:
                await cur.execute(f"CREATE DATABASE {default_db};")
                print("Database created")

            await cur.execute("SELECT 1;")

    # Modifying string to connect with dbname and executing dump file
    dsn = f"dbname={default_db} {dsn}"
    async with aiopg.connect(dsn=dsn) as conn:
        async with conn.cursor() as cur:
            print("Successfully connected")
            content = ""
            with open("aether_server/db/dump/aether.sql", "r") as file:
                content = file.read()
            await cur.execute(content)
            print("Successfully executed dump")
