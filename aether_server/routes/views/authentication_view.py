import bcrypt
import aiohttp.web as web
from sqlalchemy.future import select
from sqlalchemy import insert
import jwt

import os
import re
import datetime

from aether_server.routes.routes_decl import generic_routes
from aether_server.routes.utils import HTTP_CLIENT_APPKEY
from aether_server.db.database import POOL_APPKEY
from aether_server.db.schema import Users


class AuthenticationService:
    @staticmethod
    def verify_email(email: str) -> bool:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_regex, email) is not None

    @staticmethod
    def verify_password(password: str) -> bool:
        if len(password) < 8:
            return False

        return True

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_hashed_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


class AetherJWTManager:
    algorithm = "HS256"

    def __init__(self):
        self.secret = os.getenv("JWT_SECRET")
        self.expiry = int(os.getenv("JWT_EXPIRY", 120))
        if not self.secret:
            raise ValueError("JWT secret or expiry must be set on environment")

    def create_jwt(self, username, user_id) -> str:
        payload = {
            "sub": str(user_id),
            "username": username,
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(minutes=self.expiry),
        }
        return jwt.encode(payload, self.secret, self.algorithm)

    def decode_jwt(self, token) -> str:
        return jwt.decode(token, self.secret, self.algorithm)


@generic_routes.view("/api/authenticate-github")
class AetherGitHubAuthenticationView(web.View):
    async def get(self):
        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET")

        if client_id is None:
            raise web.HTTPServiceUnavailable(
                reason="`GITHUB_CLIENT_ID` is not set in the environment."
            )

        if client_secret is None:
            raise web.HTTPServiceUnavailable(
                reason="`GITHUB_CLIENT_SECRET` is not set in the environment."
            )

        http_client = self.request.app[HTTP_CLIENT_APPKEY]

        if "code" in self.request.query:
            async with http_client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": self.request.query["code"],
                },
                headers={
                    "Accept": "application/json",
                },
            ) as response:
                response_data = await response.json()

            async with http_client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {response_data['access_token']}",
                },
            ) as response:
                user_data = await response.json()

            return web.Response(
                text=f"Welcome, {user_data['login']}. You are now logged in."
            )

        else:
            async with http_client.get(
                "https://github.com/login/oauth/authorize",
                params={
                    "client_id": client_id,
                    "redirect_uri": str(self.request.url),
                    "scope": "read:user",
                    "allow_signup": "true",
                },
                headers={
                    "Accept": "application/json",
                },
            ) as response:
                raise web.HTTPTemporaryRedirect(response.url)


@generic_routes.view("/api/authorize-user/session")
class AetherSession(web.View):
    async def post(self):
        payload = self.request.get("user")
        return web.json_response(
            {"ok": True, "message": payload},
            status=200,
        )


@generic_routes.view("/api/authenticate-user/login")
class AetherLoginView(web.View):
    async def post(self) -> web.Response:
        data = await self.request.json()
        email = data.get("email")
        password = data.get("password")

        if not AuthenticationService.verify_email(email):
            return web.json_response(
                {"ok": False, "message": "Invalid email address"}, status=400
            )

        if not AuthenticationService.verify_password(password):
            return web.json_response(
                {"ok": False, "message": "Passwordd Invalid"}, status=400
            )
        pool = self.request.app[POOL_APPKEY]

        if not pool:
            return web.json_response(
                {
                    "ok": False,
                    "message": "Server error: Could not fetch data from the pool",
                },
                status=500,
            )

        async with pool() as session:
            try:
                stmt = select(Users).where(Users.email == email)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    return web.json_response(
                        {"ok": False, "message": "User not found. Please signup"},
                        status=404,
                    )

                if not AuthenticationService.verify_hashed_password(
                    password, user.stored_credentials
                ):
                    return web.json_response(
                        {"ok": False, "message": "Invalid password"}, status=401
                    )

                jwt_manager = AetherJWTManager()
                token = jwt_manager.create_jwt(username=user.username, user_id=user.id)
                return web.json_response(
                    {
                        "ok": True,
                        "message": "Login Successful",
                        "access_token": token,
                    },
                    status=200,
                )

            except Exception as error:
                return web.json_response(
                    {"ok": False, "message": f"Server error: {error}"}, status=500
                )


@generic_routes.view("/api/authenticate-user/signup")
class AetherSignUpView(web.View):
    async def post(self) -> web.Request:
        try:
            data = await self.request.json()
        except Exception as e:
            return web.HTTPBadRequest(reason=f"Invalid JSON Payload {e}")

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not AuthenticationService.verify_email(email):
            return web.json_response(
                {"ok": False, "message": "Invalid email address"}, status=400
            )

        if username is None:
            return web.json_response(
                {"aok": False, "message": "Username not provided"}, status=400
            )

        if not AuthenticationService.verify_password(password):
            return web.json_response(
                {
                    "ok": False,
                    "message": "Password Invalid, there should be atleast one special character",
                },
                status=400,
            )
        pool = self.request.app.get(POOL_APPKEY)

        async with pool() as session:
            try:
                stmt = select(Users).where(Users.email == email)
                results = await session.execute(stmt)
                user = results.scalar_one_or_none()

                if user is not None:
                    return web.json_response(
                        {
                            "ok": False,
                            "message": "User already exist. Please login instead.",
                        },
                        status=400,
                    )
                stored_credentials = AuthenticationService.hash_password(password)

                await session.execute(
                    insert(Users),
                    [
                        {
                            "username": username,
                            "email": email,
                            "stored_credentials": stored_credentials,
                        }
                    ],
                )
                await session.commit()
                return web.json_response(
                    {
                        "ok": True,
                        "message": "User created successfuly",
                    },
                    status=201,
                )

            except Exception as error:
                return web.json_response(
                    {"ok": False, "message": f"Server error: {error}"}, status=500
                )
