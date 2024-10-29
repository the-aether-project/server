import aiohttp.web as web
import aiohttp_jinja2

from aether_server.routes.routes_decl import generic_routes


@generic_routes.view("/")
class AetherIndexView(web.View):
    @aiohttp_jinja2.template("index.html")
    async def get(self):
        return {"ws_url": self.request.app.router["websocket"].url_for()}
