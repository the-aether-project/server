import asyncio
import pathlib

import aiohttp
import aiohttp.web as web
import aiohttp_jinja2
import jinja2

from aether_server.db import setup_database
from aether_server.routes import generic_routes
from aether_server.routes.utils import HTTP_CLIENT_APPKEY, RTC_APPKEY, RTCPeerManager

try:
    import dotenv

    dotenv.load_dotenv()
except ImportError:
    ...

try:
    import aiohttp_debugtoolbar
except ImportError:
    aiohttp_debugtoolbar = None


async def peer_manager_clearing_ctx(app: web.Application):
    app[RTC_APPKEY] = RTCPeerManager()
    yield
    await app[RTC_APPKEY].close()


async def http_client_clearing_ctx(app: web.Application):
    app[HTTP_CLIENT_APPKEY] = aiohttp.ClientSession()
    yield
    await app[HTTP_CLIENT_APPKEY].close()


def create_app(_) -> web.Application:
    project_root = pathlib.Path(__file__).parent
    asyncio.run(setup_database())
    app = web.Application()

    app.router.add_static("/static/", path=project_root / "static", name="static")
    app.add_routes(generic_routes)
    app.cleanup_ctx.extend((peer_manager_clearing_ctx, http_client_clearing_ctx))

    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(project_root / "templates")
    )

    if aiohttp_debugtoolbar is not None:
        aiohttp_debugtoolbar.setup(app, intercept_redirects=False)

    return app


if __name__ == "__main__":
    web.run_app(create_app([]), port=7878)
