import aiohttp.web as web
import aiohttp_jinja2


from aether_server.routes.routes_decl import generic_routes
import pathlib

HTML = pathlib.Path(__file__).parent.parent.parent / "index.html"


@generic_routes.view("/")
class AetherIndexView(web.View):
    @aiohttp_jinja2.template("index.html")
    async def get(self):
        ws_url = self.request.app.router["websocket"].url_for()
        print("ws url", ws_url)

        return {"ws_url": ws_url}
