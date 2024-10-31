import sys

from aiortc import RTCPeerConnection, RTCSessionDescription
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


class AetherRTC:
    def __init__(self):
        self.pc = RTCPeerConnection()

    async def initiate_Offer(self):
        if sys.platform == "win32":
            self.pc.addTrack(get_gdigrab_source())
        else:
            self.pc.addTrack(
                MediaPlayer(SAMPLE_VIDEO).video,
            )

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        return {
            "type": self.pc.localDescription.type,
            "sdp": self.pc.localDescription.sdp,
        }

    async def take_answer(self, answer_data: dict):
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        return await self.pc.setRemoteDescription(answer)

    async def close(self):
        return await self.pc.close()
