import aiohttp.web as web

from aether_server.routes.routes_decl import generic_routes


@generic_routes.view("/")
class AetherIndexView(web.View):
    async def get(self):
        return web.Response(text="Aether server is up and running.")
