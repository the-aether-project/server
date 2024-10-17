import aiohttp
from aiohttp import web
from middlewares.exceptions import NotFoundError
import json


async def websocket_handler(request):
    if not request:
        raise NotFoundError(f"Request not found - websocket request : {request}")

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == "close":
                await ws.close()
            else:
                data = json.loads(msg.data)
                print("data is", data)
                await ws.send_str(msg.data + "/answer")
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ws connection closed with expection %s" % ws.exception())

    print("Sever : websocket connection closed")
    return ws
