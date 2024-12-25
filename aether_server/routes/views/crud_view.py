from aiohttp import web
from sqlalchemy.future import select
from sqlalchemy.orm import class_mapper

from aether_server.routes.views.authentication_view import AetherJWTManager

from aether_server.routes.routes_decl import generic_routes
from aether_server.db.schema import Computers, Users
from aether_server.db.database import POOL_APPKEY

import json
import asyncio
import datetime


"""
@Private route
/api/authorized/computers

@Authorization
Bearer jwt_token

"""


@generic_routes.view("/api/authorized/computers")
class AetherComputersView(web.View):
    def serialize(self, model):
        columns = [c.key for c in class_mapper(model.__class__).columns]
        serialized_data = {}
        for c in columns:
            value = getattr(model, c)
            if isinstance(value, datetime):
                value = value.isoformat()
            serialized_data[c] = value
        return serialized_data

    async def get(self):
        payload = self.request.get("user")
        user_id = int(payload.get("sub"))
        pool = self.request.app.get(POOL_APPKEY)

        async with pool() as session:
            try:
                stmt = select(Computers).where(Computers.landlord_id == user_id)
                results = await session.execute(stmt)
                computers = results.scalars().all()

                if not computers:
                    return web.json_response(
                        {
                            "ok": False,
                            "message": "Not Found: Request data does not exist for particular user",
                        },
                        status=404,
                    )
                serialized_data = [self.serialize(computer) for computer in computers]

                return web.json_response(
                    {
                        "ok": True,
                        "message": serialized_data,
                    },
                    status=200,
                )
            except Exception as error:
                return web.json_response(
                    {"ok": False, "message": f"Unexpected error: {str(error)}"},
                    status=500,
                )


"""
@Private route
/api/authorized/identication

@Authorization
Bearer jwt_token

@returns
jwt_token

"""


@generic_routes.view("/api/authorized/identification")
class AetherIdentificationView(web.View):
    async def get(self):
        payload = self.request["user"]
        user_id = int(payload.get("sub"))
        pool = self.request.app[POOL_APPKEY]

        async with pool() as session:
            try:
                jwt_manager = AetherJWTManager()
                stmt = select(Users).where(Users.id == user_id)
                results = await session.execute(stmt)
                user = results.scalar_one_or_none()

                if not user:
                    return web.json_response(
                        {
                            "ok": False,
                            "message": "Not Found: user don't exist.",
                        },
                        status=404,
                    )

                token_pool = self.request.app["identification_token"]
                active_pool = self.request.app["active_landlords"]

                #  -> remove token if it is expired from token_pool
                #  -> remove token if particular user already has a token in a pool
                token_to_delete = []
                if len(token_pool) != 0:
                    for each_token in token_pool:
                        landlord_payload = jwt_manager.decode_jwt(each_token)
                        if jwt_manager.verify_jwt_expiry(
                            int(landlord_payload.get("exp"))
                        ) or str(landlord_payload.get("sub")) == str(user_id):
                            # token is expired
                            token_to_delete.append(each_token)

                token_pool.difference_update(token_to_delete)

                # -> Checks if user is already active with the server.
                if len(active_pool) != 0:
                    for active_token in active_pool:
                        active_payload = jwt_manager.decode_jwt(active_token)
                        landlord_id = int(active_payload.get("sub"))
                        if landlord_id == user_id:
                            break

                    if landlord_id == user_id and user.is_landlord is True:
                        return web.json_response(
                            {
                                "ok": False,
                                "message": "User is already an active landlord",
                            },
                            status=400,
                        )

                if user.is_landlord is False:
                    user.is_landlord = True
                session.add(user)
                await session.commit()

                token = jwt_manager.create_jwt(user.username, user_id)
                token_pool.add(token)

                return web.json_response(
                    {
                        "ok": True,
                        "message": token,
                    },
                    status=200,
                )

            except Exception as error:
                return web.json_response(
                    {"ok": False, "message": f"Unexpected error: {str(error)}"},
                    status=500,
                )


@generic_routes.view("/ping_pong", name="websocket")
class AetherLandlordCommunicate(web.View):
    async def get(self):
        token = self.request.query.get("token")
        token_pool = self.request.app["identification_token"]

        if not token or token not in token_pool:
            return web.json_response(
                {
                    "type": "error",
                    "message": "Invalid Token. Please login and mark yourself as landlord from the website.",
                },
                status=401,
            )
        active_pool = self.request.app["active_landlords"]
        active_pool.add(token)

        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

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
                    case "ping":
                        await asyncio.sleep(10)
                        await ws.send_json({"type": "pong"})

                    case _:
                        await ws.send_json(
                            {
                                "type": "error",
                                "message": f"Unsupported message type: {data.get("type")}",
                            }
                        )
        finally:
            active_pool.discard(token)
            await ws.close()
