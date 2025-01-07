from aiohttp import web
from sqlalchemy.future import select
from sqlalchemy.orm import class_mapper

from aether_server.routes.views.authentication_view import AetherJWTManager

from aether_server.routes.routes_decl import generic_routes
from aether_server.db.schema import Computers, Users
from aether_server.db.database import POOL_APPKEY

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

                landlords = self.request.app["landlords"]
                print(f"__LOG.__landlords are : {landlords}")

                if landlords:
                    # returning if user is already active.
                    for landlord in landlords:
                        if str(landlord["user_id"]) == user_id and landlord["active"]:
                            return web.json_response(
                                {
                                    "ok": False,
                                    "message": "User is already an active landlord",
                                },
                                status=400,
                            )
                    # - remove user if the token is already expired. For every users.
                    # - remove if this particular user is already on the list.(to avoid duplication)
                    landlords = [
                        landlord
                        for landlord in landlords
                        if not jwt_manager.verify_jwt_expiry(
                            int(
                                jwt_manager.decode_jwt(landlord["identification"]).get(
                                    "exp"
                                )
                            )
                        )
                        and jwt_manager.decode_jwt(landlord["identification"]).get(
                            "sub"
                        )
                        != str(landlord["user_id"])
                    ]

                if user.is_landlord is False:
                    user.is_landlord = True
                session.add(user)
                await session.commit()

                token = jwt_manager.create_jwt(user.username, user_id)
                # TODO: Add rate to lend the landlord computer
                landlords.append(
                    {
                        "user_id": user_id,
                        "identification": token,
                        "active": False,
                        "ws": None,
                    }
                )

                print("__LOG: After appending logs", landlords)

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
