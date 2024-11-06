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
            try:
                await cur.execute(content)
            except Exception as e:
                print(f"error: {e}")
            else:
                print("Successfully executed dump")


# For executing query call this function with params of tuples
## Eg. query = "SELECT * FROM users WHERE username = %s AND age = %s;"params = ('johndoe', 25)
async def ExecuteQuery(query, params=None):
    default_db, default_user, default_password, default_host, default_port = (
        default_credentials
    )
    dsn = f"dbname={default_db} user={default_user} password={default_password} host={default_host} port={default_port}"

    async with aiopg.connect(dsn=dsn) as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(query, params)
            except Exception as e:
                print(f"error:{e}")
            else:
                result = await cur.fetchall()
                return result
