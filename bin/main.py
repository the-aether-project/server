from aiohttp import web
from routes.routes import setup_routes
from middlewares.middleware import setup_middleware


app = web.Application()
setup_middleware(app)
setup_routes(app)
web.run_app(
    app,
    host="localhost",
    port=7878,
)
