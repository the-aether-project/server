import asyncio
import pathlib

import aiohttp.web as web
import aiohttp_jinja2
import jinja2

from aether_server.db import setup_database
from aether_server.routes import generic_routes


def create_app(_) -> web.Application:
    project_root = pathlib.Path(__file__).parent
    asyncio.run(setup_database())
    app = web.Application()

    app.router.add_static("/static/", path=project_root / "static", name="static")
    app.add_routes(generic_routes)

    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(project_root / "templates")
    )

    return app


if __name__ == "__main__":
    web.run_app(create_app([]), port=7878)
