import pathlib

import aiohttp.web as web
import aiohttp_jinja2

from aiohttp_middlewares import cors_middleware

from aether_server.core import set_context_for
from aether_server.routes import generic_routes
from aether_server.routes.views import Authorize_middleware


def create_app(_) -> web.Application:
    project_root = pathlib.Path(__file__).parent

    app = web.Application(
        middlewares=[cors_middleware(allow_all=True), Authorize_middleware]
    )

    set_context_for(app)
    app.router.add_static("/static/", path=project_root / "static", name="static")

    app.add_routes(generic_routes)

    aiohttp_jinja2.setup(
        app, loader=aiohttp_jinja2.jinja2.FileSystemLoader(project_root / "templates")
    )
    return app

if __name__ == "__main__":
    web.run_app(create_app([]), port=7878)
