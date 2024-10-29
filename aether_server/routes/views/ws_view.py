import aiohttp.web as web

import json
from aether_server.routes.routes_decl import generic_routes
from aether_server.routes.utils import AetherRtc


@generic_routes.view("/ws", name="websocket")
class AetherWSView(web.View):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)
        rtc = AetherRtc()

        async for msg in ws:
            if msg.type == web.WSMsgType.CLOSE:
                await ws.close()
                break

            try:
                data = msg.json()

                match data["type"]:
                    case "initiateOffer":
                        res = await rtc.initiate_Offer()
                        await ws.send_json({"type": "offer", "offer": res})

                    case "answer":
                        answer = data["data"]
                        rtc = await rtc.take_answer(answer)
                        await ws.send_json(
                            {"type": "msg", "msg": "connection peered up"}
                        )

                    case _:
                        await ws.send_json(
                            {
                                "type": "msg",
                                "msg": f"Aether is up and running. Data {data['type']}",
                            }
                        )

            except json.JSONDecodeError:
                await ws.send_json({"msg": "Could not decode obtained JSON."})

        return ws
