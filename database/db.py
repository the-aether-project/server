import aiopg
from aiohttp import web

from middlewares.exceptions import NotFoundError

databasedata = "dbname=aether user=root password=secret port=5432"


def go(request):
    if not request:
        raise NotFoundError("Request Not Found in index")

    print("Hello world")

    return web.Response(text=str(f"Hello world. Request"))
