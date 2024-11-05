import logging
import os
import sys
from typing import Optional

from aiortc import (
    RTCConfiguration,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaStreamTrack

SAMPLE_VIDEO = (
    "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
)


class RTCPeerManager:
    """
    Singleton RTC Peer Manager
    """

    default_stun_server = "stun:stun.l.google.com:19302"

    def __new__(cls):
        if hasattr(cls, "instance") and cls.instance is not None:
            return cls.instance

        cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self.peers: set[RTCPeerConnection] = set()

        self.logger = logging.getLogger("rtc.peermanager")
        self.__screen_relay = MediaRelay()
        self.__screen_track: Optional[MediaStreamTrack] = None

    async def create_peer(
        self, with_remote_desc: Optional[RTCSessionDescription] = None
    ):
        peer = RTCPeerConnection(
            configuration=RTCConfiguration(
                iceServers=[RTCIceServer(urls=RTCPeerManager.default_stun_server)]
            )
        )

        self.set_screen_source_for(peer)

        if with_remote_desc:
            await peer.setRemoteDescription(with_remote_desc)
            offer = await peer.createAnswer()
        else:
            offer = await peer.createOffer()

        await peer.setLocalDescription(offer)

        @peer.on("connectionstatechange")
        async def on_connectionstatechange():
            state = peer.connectionState

            if state in ("closed", "failed"):
                self.peers.discard(peer)
                self.logger.info("Peer %d discarded.", id(peer))

                if not self.peers:
                    self.logger.info(
                        "Clearing screen sources because of no active peers."
                    )
                    self.reset_screen_source()

                return await peer.close()

            if state == "connected":
                self.logger.info("Peer %d connected.", id(peer))
                self.peers.add(peer)

        return peer

    def reset_screen_source(self):
        if self.__screen_track is not None:
            self.__screen_track.stop()
            self.__screen_track = None

    def set_screen_source_for(self, peer: RTCPeerConnection):
        if self.__screen_track is None:
            if sys.platform == "win32":
                player = MediaPlayer(
                    "desktop",
                    format="gdigrab",
                    options={
                        "framerate": "60",
                    },
                )
            elif sys.platform == "linux":
                player = MediaPlayer(
                    f"{os.getenv('DISPLAY')}.0",
                    format="x11grab",
                    options={
                        "video_size": "1920x1080",
                        "framerate": "60",
                    },
                )
            else:
                self.logger.warn(
                    "Screen-mirroring is not supported for %r.", sys.platform
                )

                player = MediaPlayer(SAMPLE_VIDEO)

            self.__screen_track = player.video

        peer.addTrack(self.__screen_relay.subscribe(self.__screen_track))

    async def close(self):
        for peer in self.peers:
            await peer.close()

        self.reset_screen_source()
        self.peers.clear()

    @staticmethod
    def create_session_description(sdp: str, type: str):
        return RTCSessionDescription(sdp=sdp, type=type)
