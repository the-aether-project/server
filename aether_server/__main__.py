import aiohttp.web as web
import aiohttp_jinja2
import jinja2

from aether_server.routes import generic_routes

import pathlib

BASE_DIR = pathlib.Path(__file__).parent


def create_app(_) -> web.Application:
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("aether_server"))

    app.router.add_static("/static/", path=str(BASE_DIR / "static"), name="static")
    app.add_routes(generic_routes)

    return app


if __name__ == "__main__":
    web.run_app(create_app([]), port=7878)
