import json

import aiohttp.web as web

from aether_server.routes.routes_decl import generic_routes
from aether_server.routes.utils import RTC_APPKEY

try:
    import pyautogui
except ImportError:
    pyautogui = None


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
                case "startConnection":
                    await ws.send_json(
                        {
                            "type": "negotiate",
                            "stun_server": peer_manager.default_stun_server,
                        }
                    )

                case "offer":
                    payload = data["payload"]

                    peer = await peer_manager.create_peer(
                        peer_manager.create_session_description(**payload)
                    )

                    await ws.send_json(
                        {
                            "type": "remoteDescription",
                            "answer": {
                                "sdp": peer.localDescription.sdp,
                                "type": peer.localDescription.type,
                            },
                        }
                    )

                case "closeConnection":
                    if peer is not None:
                        await peer.close()
                        peer = None
                        await ws.send_json({"type": "msg", "msg": "Connection closed."})
                    break
                case "mouse":
                    logger = peer_manager.logger.getChild(f"peer-0x{id(peer):0x}")
                    logger.info("Mouse event: %s", data["payload"])

                    if pyautogui is not None:
                        width, height = pyautogui.size()

                        current_pos = pyautogui.position()

                        logger.info(
                            "Clicked at: x=%f, y=%f",
                            data["payload"]["clicked_at"]["x_ratio"] * width,
                            data["payload"]["clicked_at"]["y_ratio"] * height,
                        )
                        pyautogui.leftClick(
                            x=data["payload"]["clicked_at"]["x_ratio"] * width,
                            y=data["payload"]["clicked_at"]["y_ratio"] * height,
                        )

                        pyautogui.moveTo(*current_pos)

                case _:
                    await ws.send_json(
                        {
                            "type": "msg",
                            "msg": f"Unsupported message type: {data['type']}",
                        }
                    )

        if peer is not None:
            await peer.close()

        await ws.close()
        return ws
