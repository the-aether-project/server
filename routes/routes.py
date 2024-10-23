from aiohttp import web

from controllers import index, websocket_handler
from database import go


def setup_routes(app):
    app.router.add_get("/", index)
    app.add_routes([web.get("/ws", websocket_handler)])
    app.router.add_get("/test", go)
