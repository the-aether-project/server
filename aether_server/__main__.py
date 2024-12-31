import aiohttp.web as web
from aiohttp_middlewares import cors_middleware

from aether_server.core import set_context_for
from aether_server.routes import generic_routes
from aether_server.routes.views import Authorize_middleware


def create_app(_) -> web.Application:

    app = web.Application(
        middlewares=[cors_middleware(allow_all=True), Authorize_middleware]
    )

    set_context_for(app)

    app.add_routes(generic_routes)

    return app


if __name__ == "__main__":
    web.run_app(create_app([]), port=7878)
