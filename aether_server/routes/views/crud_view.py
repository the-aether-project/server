from aiohttp import web
from sqlalchemy.future import select
from sqlalchemy.orm import class_mapper

from datetime import datetime

from aether_server.routes.routes_decl import generic_routes
from aether_server.db.schema import Computers
from aether_server.db.database import POOL_APPKEY


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
        if not self.request["user"]:
            return web.json_response(
                {"ok": False, "message": "Failed to get User information"}, status=500
            )
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
                            "message": "Request data does not exist for particular user",
                        },
                        status=400,
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
