import pathlib

import aiohttp.web as web
import aiohttp_jinja2
import jinja2

from aether_server.routes import generic_routes
from aether_server.routes.utils import RTC_APPKEY, RTCPeerManager


async def peer_manager_clearing_ctx(app: web.Application):
    app[RTC_APPKEY] = RTCPeerManager()
    yield
    await app[RTC_APPKEY].close()


def create_app(_) -> web.Application:
    project_root = pathlib.Path(__file__).parent

    app = web.Application()

    app.router.add_static("/static/", path=project_root / "static", name="static")
    app.add_routes(generic_routes)
    app.cleanup_ctx.append(peer_manager_clearing_ctx)

    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(project_root / "templates")
    )

    return app


if __name__ == "__main__":
    web.run_app(create_app([]), port=7878)
