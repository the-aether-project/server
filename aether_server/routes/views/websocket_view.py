from aiohttp import web
import asyncio
import jwt

from aether_server.routes import generic_routes
from aether_server.routes.views.authentication_view import AetherJWTManager

import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LandlordManager:
    def __init__(self, ws, selected_landlord):
        self.__ws = ws
        self.__Ilandlord = selected_landlord

    async def __send_json(self, data):
        if self.__ws is not None:
            return await self.__ws.send_json(data)

    async def control_release(self, data):
        if "ws_client" in self.__Ilandlord or self.__Ilandlord["ws_client"] is not None:
            await self.__Ilandlord["ws_client"].send_json(data)

    async def disconnection(self, data):
        if "ws_client" in self.__Ilandlord:
            await self.__Ilandlord["ws_client"].send_json(data)

    async def ping_manager(self):
        async def ping():
            await asyncio.sleep(10)  # 10 seconds
            await self.__send_json({"type": "PING"})

        asyncio.create_task(ping())

    async def connection_made(self, answer):
        self.__Ilandlord["active"] = True
        if (
            "ws_client" in self.__Ilandlord
            and self.__Ilandlord["ws_client"] is not None
        ):
            await self.__Ilandlord["ws_client"].send_json(
                {
                    "type": "ANSWER",
                    "sdp": answer,
                }
            )

    async def specification(self, data, landlords_specs, clients):
        landlords_specs.append(
            {"landlord_id": self.__Ilandlord["user_id"], "info": data}
        )
        dead_clients = set()

        # Sending all the specs details to all the active clients to be able to showcase in dashboard(frontend)
        async def notify(each_ws):
            try:
                await each_ws.send_json({"type": "DEVICES", "devices": landlords_specs})
            except (ConnectionAbortedError, ConnectionResetError):
                logger.warning(f"___ Warning -> User with ws {each_ws} not active")
                dead_clients.add(each_ws)

        results = asyncio.gather(
            *(notify(ws) for ws in clients), return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"___Warning -> Notification failed: {result}")

        if dead_clients:
            clients.difference_update(dead_clients)
            dead_clients.clear()

    async def prune(self):
        self.__Ilandlord = None
        await self.__ws.close()
        logger.info("___Info -> Landlord websocket connection pruned!")
        return


"""
- Websocket connection for landlord

@requires,

@query,
?token=<identification token>
"""


@generic_routes.view("/v1/landlord/ws", name="websocket")
class AetherLandlordCommunicate(web.View):
    async def get(self):
        # validating identification token from query
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

        # landlord should be on server memory when requesting identification token(more: crud_view.py)
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
        await ws.prepare(self.request)

        selected_landlord["ws"] = ws
        landlord_manager = LandlordManager(ws, selected_landlord)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.CLOSE:
                    logger.info("__Websocket closed on this landlord")
                    return await ws.close()
                try:
                    data = msg.json()
                except json.JSONDecodeError as e:
                    await ws.send_json(
                        {"type": "error", "message": f"Could not decode json. {e}"}
                    )
                    continue

                match data["type"]:
                    # As soon as the landlord is active, landlord's specs should be available
                    case "SPECIFICATION":
                        await landlord_manager.specification(
                            data.get("message"),
                            self.request.app["landlord_specification"],
                            self.request.app["clients"],
                        )

                    case "CONTROL_RELEASED":
                        await landlord_manager.control_release(
                            {
                                "type": "CONTROL_ACK",
                                "uuid": data.get("uuid"),
                            }
                        )

                    case "DISCONNECTION_MADE":
                        await landlord_manager.disconnection(
                            {
                                "type": "DISCONNECT_ACK",
                                "uuid": data.get("uuid"),
                            }
                        )

                    case "PONG":
                        await landlord_manager.ping_manager()

                    # WebRTC Answer from landlord, should be forwarded to the client
                    case "CONNECTION_MADE":
                        if data["sdp_answer"]:
                            await landlord_manager.connection_made(data["sdp_answer"])

                    case _:
                        await ws.send_json(
                            {
                                "type": "error",
                                "message": f"Unsupported message type: {data.get('type')}",
                            }
                        )

        finally:
            if selected_landlord in landlords:
                landlords.remove(selected_landlord)
                await landlord_manager.prune()

        return ws


"""
- Websocket connection for client

@requires,

@query,
?token=<auth token>
"""


class ClientManager:
    def __init__(self, ws, landlords, payload) -> None:
        self.__ws = ws
        self.landlords = landlords
        self.user_payload = payload

    async def __send_json(self, data):
        if self.__ws is not None:
            return await self.__ws.send_json(data)

    def my_landlord(self, landlord_id):
        return next(
            (
                landlord
                for landlord in self.landlords
                if landlord["user_id"] == landlord_id
            ),
            None,
        )

    async def offer(self, offer, landlord_id):
        selected_landlord = self.my_landlord(landlord_id)
        if selected_landlord is None or selected_landlord["active"]:
            await self.__send_json(
                {
                    "type": "ERROR",
                    "message": "Landlord is either not present or Already active with some other user",
                }
            )

        ws_landlord = selected_landlord["ws"]
        if ws_landlord is None:
            return await self.__send_json(
                {"type": "ERROR", "message": "Landlord is not active anymore"}
            )

            # TODO: UUID to identify the client_id
            # sending sdp offer to the landlord
        selected_landlord["ws_client"] = self.__ws
        return await ws_landlord.send_json(
            {
                "type": "CONNECTION",
                "offer": offer,
                "uuid": str(self.user_payload.get("sub")),
            }
        )

    async def control(self, landlord_id):
        selected_landlord = self.my_landlord(landlord_id)
        if selected_landlord is None:
            await self.__send_json(
                {"type": "ERROR", "message": "Could not find the your landlord"}
            )

        ws_landlord = selected_landlord["ws"]
        if ws_landlord is None:
            return await self.__send_json(
                {"type": "ERROR", "message": "landlord is not active anymore"}
            )

        if "ws_client" not in selected_landlord:
            selected_landlord["ws_client"] = self.__ws

        await ws_landlord.send_json(
            {"type": "CONTROL", "uuid": self.user_payload.get("sub")}
        )

    async def disconnect(self, landlord_id):
        selected_landlord = self.my_landlord(landlord_id)
        if selected_landlord is None:
            await self.__send_json(
                {"type": "ERROR", "message": "Could not find your landlord"}
            )

        ws_landlord = selected_landlord["ws"]
        if ws_landlord is None:
            return await self.__send_json(
                {"type": "ERROR", "message": "landlord is not active anymore"}
            )

        if "ws_client" not in selected_landlord:
            selected_landlord["ws_client"] = self.__ws

        await ws_landlord.send_json(
            {"type": "DISCONNECT", "uuid": str(self.user_payload.get("sub"))}
        )

    async def prune(self):
        if self.__ws is not None:
            logger.info(
                f"___Log -> Client Websocket pruned id: {self.user_payload["sub"]}"
            )
            await self.__ws.close()
            self.__ws = None


@generic_routes.view("/v1/clients/ws")
class AetherClientWebSocketView(web.View):
    async def get(self):
        # Client authorization token
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

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return web.json_response(
                {
                    "ok": False,
                    "message": "Token Invalid or expired, Please Try again.",
                },
                status=400,
            )

        ws = web.WebSocketResponse(timeout=60)  # 60 seconds timeout
        await ws.prepare(self.request)

        self.request.app["clients"].add(ws)
        landlords = self.request.app["landlords"]
        client_manager = ClientManager(ws, landlords, user_payload)

        await ws.send_json(
            {"type": "WS_CONNECTION", "message": "Connection established"}
        )

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.CLOSE:
                    await ws.close()
                    logger.info("__Websocket closed on this Client")
                    break
                try:
                    data = msg.json()
                except json.JSONDecodeError as e:
                    await client_manager.__send_json(
                        {"type": "error", "message": f"Could not decode json. {e}"}
                    )

                match data["type"]:
                    case "OFFER":
                        await client_manager.offer(
                            data.get("offer"), data.get("landlord_id")
                        )

                    case "CONTROL":
                        await client_manager.control(data.get("landlord_id"))

                    case "DISCONNECT":
                        await client_manager.disconnect(data.get("landlord_id"))

                    case _:
                        await ws.send_json(
                            {
                                "type": "error",
                                "message": f"Unsupported message type: {data.get('type')}",
                            }
                        )

        finally:
            if ws in self.request.app["clients"]:
                self.request.app["clients"].remove(ws)

            await client_manager.prune()

        return ws
