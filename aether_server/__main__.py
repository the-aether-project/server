import aiohttp.web as web

from aether_server.routes import generic_routes


def create_app(_) -> web.Application:
    app = web.Application()
    app.add_routes(generic_routes)

    return app


if __name__ == "__main__":
    web.run_app(create_app([]), port=7878)
