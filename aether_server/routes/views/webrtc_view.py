import aiohttp.web as web
from aether_server.routes.routes_decl import generic_routes
from aether_server.routes.utils import RTC_APPKEY


@generic_routes.view("/api/authorized/webrtc-offer")
class AetherWebRTCView(web.View):
    async def post(self):
        data = await self.request.json()

        peer_manager = self.request.app[RTC_APPKEY]
        peer = await peer_manager.create_peer(
            peer_manager.create_session_description(**data)
        )

        return web.json_response(
            {
                "sdp": peer.localDescription.sdp,
                "type": peer.localDescription.type,
            }
        )
