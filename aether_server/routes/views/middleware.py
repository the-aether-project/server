from aiohttp import web
from .authentication_view import AetherJWTManager
import jwt


@web.middleware
async def Authorize_middleware(request, handler):
    public_routes = [
        "/api/authenticate-user/signup",
        "/api/authenticate-user/login",
        "/api/authenticate-github",
    ]

    if request.path in public_routes:
        return await handler(request)

    auth_token = request.headers.get("Authorization")
    if auth_token and auth_token.startswith("Bearer"):
        token = auth_token.split(" ")[1]
        try:
            jwt_manager = AetherJWTManager()
            payload = jwt_manager.decode_jwt(token)
            request["user"] = payload
            return await handler(request)

        except jwt.ExpiredSignatureError:
            return web.json_response(
                {"ok": False, "message": "Token expired, Please login again"},
                status=401,
            )
        except jwt.InvalidTokenError:
            return web.json_response(
                {"ok": False, "message": "Invalid token"}, status=403
            )
    else:
        return web.json_response(
            {
                "ok": False,
                "message": "Authentication token is missing",
            },
            status=401,
        )
