import json

import aiohttp.web as web

from aether_server.routes.routes_decl import generic_routes
from aether_server.routes.utils import AetherRTC


@generic_routes.view("/ws", name="websocket")
class AetherWSView(web.View):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)
        rtc = AetherRTC()

        async for msg in ws:
            if msg.type == web.WSMsgType.CLOSE:
                await ws.close()
                break

            try:
                data = msg.json()
            except json.JSONDecodeError:
                await ws.send_json({"msg": "Could not decode obtained JSON."})
                continue

            match data["type"]:
                case "initiateOffer":
                    await ws.send_json(
                        {"type": "offer", "offer": await rtc.initiate_Offer()}
                    )

                case "answer":
                    await rtc.take_answer(data["payload"])
                    await ws.send_json({"type": "msg", "msg": "Connection commencing."})

                case _:
                    await ws.send_json(
                        {
                            "type": "msg",
                            "msg": f"Unsupported message type: {data['type']}",
                        }
                    )

        await rtc.close()
        return ws
