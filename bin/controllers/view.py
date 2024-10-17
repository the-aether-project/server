from aiohttp import web
from middlewares.exceptions import NotFoundError


def index(request):
    if not request:
        raise NotFoundError("Request Not Found in index")

    return web.Response(text=str(f"Hello world. Request {request.method}"))
