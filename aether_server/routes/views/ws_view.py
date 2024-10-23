import json

import aiohttp.web as web

from aether_server.routes.routes_decl import generic_routes


@generic_routes.view("/ws")
class AetherWSView(web.View):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        async for msg in ws:
            if msg.type == web.WSMsgType.CLOSE:
                await ws.close()
                break

            try:
                data = msg.json()
                await ws.send_json(
                    {"message": "Aether is up and running.", "answer": data}
                )
            except json.JSONDecodeError:
                await ws.send_str({"message": "Could not decode obtained JSON."})

        return ws
