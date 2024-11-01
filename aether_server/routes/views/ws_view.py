import json

import aiohttp.web as web

from aether_server.routes.routes_decl import generic_routes
from aether_server.routes.utils import RTC_APPKEY


@generic_routes.view("/ws", name="websocket")
class AetherWSView(web.View):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        peer_manager = self.request.app[RTC_APPKEY]
        peer = None

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
                    peer = await peer_manager.create_peer()

                    await ws.send_json(
                        {
                            "type": "offer",
                            "offer": {
                                "sdp": peer.localDescription.sdp,
                                "type": peer.localDescription.type,
                            },
                            "stun_server": peer_manager.default_stun_server,
                        }
                    )

                case "answer":
                    payload = data["payload"]

                    await peer.setRemoteDescription(
                        peer_manager.create_session_description(**payload)
                    )

                    await ws.send_json(
                        {"type": "msg", "msg": "Attempting to start connection."}
                    )

                case "closeConnection":
                    if peer is not None:
                        await peer.close()
                        peer = None
                        await ws.send_json({"type": "msg", "msg": "Connection closed."})

                case _:
                    await ws.send_json(
                        {
                            "type": "msg",
                            "msg": f"Unsupported message type: {data['type']}",
                        }
                    )

        if peer is not None:
            await peer.close()
        return ws
