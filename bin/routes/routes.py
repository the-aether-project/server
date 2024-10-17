from controllers import index, websocket_handler
from aiohttp import web


def setup_routes(app):
    app.router.add_get("/", index)
    app.add_routes([web.get("/ws", websocket_handler)])
