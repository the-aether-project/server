from aiohttp import web
from .authentication_view import AetherJWTManager
import jwt


"""
Public path are any that does not start with "/api/authorized"
"""


@web.middleware
async def Authorize_middleware(request, handler):
    if not request.path.startswith("/api/authorized"):
        return await handler(request)

    auth_token = request.headers.get("Authorization")

    if auth_token and auth_token.startswith("Bearer"):
        token = auth_token.split(" ")[1]
        try:
            jwt_manager = AetherJWTManager()
            payload = jwt_manager.decode_jwt(token)
            request["user"] = payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return web.json_response(
                {
                    "ok": False,
                    "message": "Token either Invalid or Expired, Please login again",
                },
                status=400,
            )

    else:
        return web.json_response(
            {
                "ok": False,
                "message": "Authorization token is missing",
            },
            status=401,
        )
    return await handler(request)
