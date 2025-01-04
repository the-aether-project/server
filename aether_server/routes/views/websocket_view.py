from aiohttp import web
import asyncio
import jwt

from aether_server.routes import generic_routes
from aether_server.routes.views.authentication_view import AetherJWTManager
from aether_server.routes.views.webrtc_view import AetherWebRTCView

import json


@generic_routes.view("/v1/landlord/ws", name="websocket")
class AetherLandlordCommunicate(web.View):
    async def get(self):
        token = self.request.query.get("token")
        if token is None:
            return web.json_response(
                {
                    "type": "error",
                    "message": "Please include the token in the query of websocket",
                },
                status=401,
            )
        landlords = self.request.app["landlords"]

        selected_landlord = next(
            (landlord for landlord in landlords if landlord["identification"] == token),
            None,
        )

        # error when token does not match any landlords in server memory
        if selected_landlord is None:
            return web.json_response(
                {
                    "type": "error",
                    "message": "Invalid Token. Please login and mark yourself as landlord from the website.",
                },
                status=401,
            )
        ws = web.WebSocketResponse(timeout=60)  # 60 seconds timeout
        try:
            await ws.prepare(self.request)
        except Exception as e:
            return web.json_response(
                {
                    "type": "error",
                    "message": f"Could not prepare websocket connection {e}",
                },
                status=500,
            )

        selected_landlord["ws"] = ws

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.CLOSE:
                    return await ws.close()
                try:
                    data = msg.json()
                except json.JSONDecodeError as e:
                    await ws.send_json(
                        {"type": "error", "message": f"Could not decode json. {e}"}
                    )

                match data["type"]:
                    case "SPECIFICATION":
                        # receives data from landlord, forward it with landlord's user_id to frontend
                        landlords_device = self.request.app["landlord_specification"]
                        landlords_device.append(
                            {
                                "landlord_id": selected_landlord["user_id"],
                                "info": data.get("message"),
                            }
                        )

                        active_clients = self.request.app["clients"]
                        dead_clients = set()

                        async def send_info(ws):
                            try:
                                await ws.send_json(
                                    {"type": "DEVICES", "devices": landlords_device}
                                )
                            except (ConnectionResetError, ConnectionError):
                                dead_clients.add(ws)

                        asyncio.gather(
                            *(send_info(ws) for ws in active_clients),
                            return_exceptions=True,
                        )

                        if dead_clients:
                            active_clients.difference_update(dead_clients)
                            dead_clients.clear()

                    case "CONTROL_RELEASED":
                        await selected_landlord["ws_client"].send_json(
                            {
                                "type": "CONTROL_ACK",
                                "uuid": data.get("uuid"),
                            }
                        )
                    case "DISCONNECTION_MADE":
                        if "ws_client" in selected_landlord:
                            ws_client = selected_landlord["ws_client"]
                            await ws_client.send_json(
                                {
                                    "type": "DISCONNECT_ACK",
                                    "uuid": ws.get("uuid"),
                                }
                            )

                    case "ping":
                        asyncio.create_task(self.ping_response(ws))

                    case "CONNECTION_MADE":
                        answer = data["sdp_answer"]
                        if answer:
                            selected_landlord["active"] = True
                            if "ws_client" in selected_landlord:
                                ws_client = selected_landlord["ws_client"]
                                await ws_client.send_json(
                                    {
                                        "type": "ANSWER",
                                        "sdp": answer,
                                    }
                                )

                    case _:
                        await ws.send_json(
                            {
                                "type": "error",
                                "message": f"Unsupported message type: {data.get('type')}",
                            }
                        )

        finally:
            await ws.close()
            selected_landlord["active"] = False
            selected_landlord["ws"] = None

    async def ping_response(ws):
        await asyncio.sleep(10)
        await ws.send_json({"type": "pong"})


@generic_routes.view("/v1/clients/ws")
class AetherClientWebSocketView(web.View):
    async def get(self):
        # this token is of user.
        token = self.request.query.get("token") or None

        if token is None:
            return web.json_response(
                {
                    "ok": False,
                    "message": "Authorization token is missing",
                },
                status=401,
            )

        try:
            jwt_manager = AetherJWTManager()
            user_payload = jwt_manager.decode_jwt(token)
        except jwt.ExpiredSignatureError:
            return web.json_response(
                {"ok": False, "message": "Token expired, Please login again"},
                status=401,
            )
        except jwt.InvalidTokenError:
            return web.json_response(
                {"ok": False, "message": "Invalid token"}, status=403
            )

        ws = web.WebSocketResponse(timeout=60)  # 60 seconds timeout
        await ws.prepare(self.request)

        self.request.app["clients"].add(ws)

        await ws.send_json(
            {"type": "WS_CONNECTION", "message": "Connection established"}
        )

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.CLOSE:
                    await ws.close()
                    break
                try:
                    data = msg.json()
                except json.JSONDecodeError as e:
                    await ws.send_json(
                        {"type": "error", "message": f"Could not decode json. {e}"}
                    )
                match data["type"]:
                    case "OFFER":
                        # when user click on rent,
                        landlords = self.request.app["landlords"]
                        webrtc_manager = AetherWebRTCView()

                        await webrtc_manager.post(
                            landlords,
                            ws_client=ws,
                            client_id=user_payload.get("sub"),
                            offer=data.get("offer"),
                            landlord_id=data.get("landlord_id"),
                        )

                    case "CONTROL":
                        landlords = self.request.app["landlords"]

                        selected_landlord = next(
                            (
                                landlord
                                for landlord in landlords
                                if landlord["user_id"] == data.get("landlord_id")
                            ),
                            None,
                        )

                        if selected_landlord is None:
                            await ws.send_json(
                                {
                                    "type": "ERROR",
                                    "message": "Could not find the active landlord",
                                }
                            )

                        ws_landlord = selected_landlord["ws"]
                        if ws_landlord is None:
                            return await ws.send_json(
                                {
                                    "type": "ERROR",
                                    "message": "landlord is not active anymore",
                                }
                            )

                        if "ws_client" not in selected_landlord:
                            selected_landlord["ws_client"] = ws

                        await ws_landlord.send_json(
                            {"type": "CONTROL", "uuid": user_payload.get("sub")}
                        )

                    case "DISCONNECT":
                        client_id = user_payload.get("sub")
                        landlord_id = data.get("landlord_id")
                        landlords = self.request.app["landlords"]

                        selected_landlord = None
                        for landlord in landlords:
                            if landlord["user_id"] == landlord_id:
                                selected_landlord = landlord
                                break

                        if selected_landlord is None:
                            await ws.send_json(
                                {
                                    "type": "ERROR",
                                    "message": "Could not find the active landlord",
                                }
                            )

                        ws_landlord = selected_landlord["ws"]
                        if ws_landlord is None:
                            return await ws.send_json(
                                {
                                    "type": "ERROR",
                                    "message": "landlord is not active anymore",
                                }
                            )

                        if "ws_client" not in selected_landlord:
                            selected_landlord["ws_client"] = ws

                        await ws_landlord.send_json(
                            {"type": "DISCONNECT", "uuid": str(client_id)}
                        )
                    case _:
                        await ws.send_json(
                            {
                                "type": "error",
                                "message": f"Unsupported message type: {data.get('type')}",
                            }
                        )

        finally:
            await ws.close()
