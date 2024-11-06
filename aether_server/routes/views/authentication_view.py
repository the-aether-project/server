import os

import aiohttp.web as web

from aether_server.routes.routes_decl import generic_routes
from aether_server.routes.utils import HTTP_CLIENT_APPKEY


@generic_routes.view("/authenticate-github")
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
