import asyncio
import os
import sys
from contextlib import suppress

import aiohttp
import aiohttp.web as web
import aiopg

from .db import POOL_APPKEY, schema_path, try_fetch_login_params_from_env
from .routes.utils import HTTP_CLIENT_APPKEY, RTC_APPKEY, RTCPeerManager


def set_windows_loop_policy():
    if sys.platform == "win32":
        print(
            "Selector policy is in use for aiopg on Windows.\n"
            "This policy is known to mishandle signals.\n"
            f"Please kill the process with PID {os.getpid()} if required.",
            file=sys.__stderr__,
        )
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class AetherContext:
    """
    Project-only context creation for
    `aiohttp.web.Application`.
    """

    def __init__(self, app: web.Application, use_database: bool = False):
        self.app = app
        self.use_database = use_database

        self.__rtc_peer_manager = None
        self.__http_client = None

        self.__database_pool = None

        self.app.on_shutdown.append(lambda _: self.close())

    async def __setup_rtc_peer_manager(self):
        self.__rtc_peer_manager = RTCPeerManager()
        self.app[RTC_APPKEY] = self.__rtc_peer_manager

    async def __setup_http_client(self):
        self.__http_client = aiohttp.ClientSession(
            headers={"User-Agent": "Aether/1.0 (unreleased)"}
        )
        self.app[HTTP_CLIENT_APPKEY] = self.__http_client

    async def __setup_database(self):
        self.__database_pool = await aiopg.create_pool(
            try_fetch_login_params_from_env()
        )
        async with self.__database_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(schema_path.read_text(encoding="utf-8"))

        self.app[POOL_APPKEY] = self.__database_pool

    def __call__(self, *args, **kwds):
        return self

    async def create(self):
        setup_coros = [
            self.__setup_rtc_peer_manager,
            self.__setup_http_client,
        ]

        if self.use_database:
            setup_coros.append(self.__setup_database)

        for setup_coro in setup_coros:
            await setup_coro()

        yield
        await self.close()

    async def close(self):
        if self.__rtc_peer_manager is not None:
            await self.__rtc_peer_manager.close()

        if self.__http_client is not None:
            await self.__http_client.close()

        if self.__database_pool is not None:
            self.__database_pool.close()
            await self.__database_pool.wait_closed()


def set_context_for(app: web.Application, development_mode=True):
    if development_mode:
        with suppress(ImportError):
            import dotenv

            dotenv.load_dotenv()

        with suppress(ImportError):
            import aiohttp_debugtoolbar

            aiohttp_debugtoolbar.setup(app, intercept_redirects=False)

    use_database = os.getenv("USE_DATABASE", "0") == "1"

    if use_database:
        set_windows_loop_policy()

    app.cleanup_ctx.append(
        lambda app: AetherContext(app, use_database=use_database).create()
    )
