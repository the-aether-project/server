import sys

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceServer,
    RTCConfiguration,
)
from aiortc.contrib.media import MediaPlayer

SAMPLE_VIDEO = (
    "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
)
GDIGRAB_DEFAULT_OPTIONS = {
    "framerate": "60",
    "pixel_format": "bgr24",
    "scale": "1280:720",
}


def get_gdigrab_source(screen="desktop", options=None, **kwargs):
    return MediaPlayer(
        screen,
        format="gdigrab",
        options=options or GDIGRAB_DEFAULT_OPTIONS,
        **kwargs,
    ).video


X11GRAB_DEFAULT_OPTIONS = {
    "video_size": "1920x1030",
    "framerate": "50",
    "draw_mouse": "1",
}


def get_x11grab_source(screen=":1.0", options=None, **kwargs):
    return MediaPlayer(
        screen,
        format="x11grab",
        options=options or X11GRAB_DEFAULT_OPTIONS,
        **kwargs,
    ).video


class AetherRTC:
    def __init__(self):
        config = RTCConfiguration(
            iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
        )
        self.pc = RTCPeerConnection(configuration=config)

    async def initiate_Offer(self):
        if sys.platform == "win32":
            self.pc.addTrack(get_gdigrab_source())
        elif sys.platform == "linux":
            # print("x11 grab : ", vars(get_x11grab_source()))
            self.pc.addTrack(get_x11grab_source())
        else:
            self.pc.addTrack(
                MediaPlayer(SAMPLE_VIDEO).video,
            )

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is %s" % self.pc.connectionState)
            if self.pc.connectionState == "failed":
                await self.pc.close()

        return {
            "type": self.pc.localDescription.type,
            "sdp": self.pc.localDescription.sdp,
        }

    async def take_answer(self, answer_data: dict):
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        return await self.pc.setRemoteDescription(answer)

    async def close(self):
        return await self.pc.close()
