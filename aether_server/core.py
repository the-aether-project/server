import asyncio
import os
import sys
from contextlib import suppress

import aiohttp
import aiohttp.web as web
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .db import POOL_APPKEY, Base, trigger_total_cost, try_fetch_login_params_from_env


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

        self.__database_pool = None
        self.__database_engine = None

        """
        landlord=[
        {
            "user_id": user_id,
            "identification": token,
            "active": False,
            "ws": None,
            "ws_client": None,
        }
        ]
        """
        self.app["landlords"] = []
        self.app["landlord_specification"] = []
        self.app["clients"] = set()

        self.app.on_shutdown.append(lambda _: self.close())

    async def __setup_http_client(self):
        self.__http_client = aiohttp.ClientSession(
            headers={"User-Agent": "Aether/1.0 (unreleased)"}
        )

    async def __setup_database(self):
        self.__database_engine = create_async_engine(
            try_fetch_login_params_from_env(),
            echo=True,
        )
        try:
            async with self.__database_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                trigger_total_cost(Base)
            print("Database tables Initialized successfully")
        except Exception as error:
            print(
                f"Error occured on Initialising Database engine.\n Check if postgres server is ready for connection{error}"
            )
            raise

        self.__database_pool = sessionmaker(
            self.__database_engine, expire_on_commit=False, class_=AsyncSession
        )
        self.app[POOL_APPKEY] = self.__database_pool

    def __call__(self, *args, **kwds):
        return self

    async def create(self):
        setup_coros = [
            self.__setup_http_client,
        ]
        if self.use_database:
            setup_coros.append(self.__setup_database)

        for setup_coro in setup_coros:
            await setup_coro()

        yield
        await self.close()

    async def close(self):
        if self.__http_client is not None:
            await self.__http_client.close()

        if self.__database_engine is not None:
            await self.__database_engine.dispose()


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
