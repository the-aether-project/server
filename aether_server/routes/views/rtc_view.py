from aiortc import RTCPeerConnection, RTCSessionDescription
from aiohttp import web

from aether_server.routes.routes_decl import generic_routes
import json


@generic_routes.view("/rtc")
class AetherRtcView(web.View):
    async def post(self):
        print("for real")
        try:
            body = await self.request.json()
            offer = RTCSessionDescription(body["sdp"], body["type"])

            pc = RTCPeerConnection()
            pc.setRemoteDescription(offer)

            # TODO :get video stream from window capture.
            # video_track = VideoTrack()
            # pc.addTrack(video_track)

            answer = await pc.createAnswer()
            pc.setLocalDescription(answer)

            return web.Response(
                content_type="application/json",
                text=json.dumps(
                    {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
                ),
            )

        except Exception as e:
            print(f"Error occured on RTC processing in server,  , {e}")
