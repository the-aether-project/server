from aiohttp import web

from database.db import handle
from middlewares.middleware import setup_middleware
from routes.routes import setup_routes

app = web.Application()
setup_middleware(app)
setup_routes(app)
web.run_app(app, port=7878)
