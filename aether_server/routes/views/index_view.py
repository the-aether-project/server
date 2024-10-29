import aiohttp.web as web

from aether_server.routes.routes_decl import generic_routes
import pathlib

HTML = pathlib.Path(__file__).parent.parent.parent / "index.html"


@generic_routes.view("/")
class AetherIndexView(web.View):
    async def get(self):
        contents = open(HTML, "r").read()
        return web.Response(content_type="text/html", text=contents)
