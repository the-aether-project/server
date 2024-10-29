import asyncio
import threading
from typing import Tuple

import cv2
import windows_capture
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame

SAMPLE_VIDEO = (
    "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
)


class ScreenStreamTrack(VideoStreamTrack):
    def __init__(self, frame_rate: int = 60, resize_to: Tuple[int, int] = (1280, 720)):
        super().__init__()

        self.frame_rate = frame_rate
        self.resize_to = resize_to

        self.capture = windows_capture.WindowsCapture(draw_border=False)

        self.__last_frame = None

        @self.capture.event
        def on_frame_arrived(
            frame: windows_capture.Frame,
            capture_control: windows_capture.InternalCaptureControl,
        ):
            # NOTE
            # The screenshot is in BGRA format.
            # PyAV does not support alpha channels.
            buffer = frame.convert_to_bgr().frame_buffer

            if self.resize_to:
                buffer = cv2.resize(buffer, self.resize_to)

            self.__last_frame = buffer

        @self.capture.event
        def on_closed():
            ...

        threading.Thread(target=self.capture.start).start()

    async def recv(self):
        if self.__last_frame is not None:
            video_frame = VideoFrame.from_ndarray(self.__last_frame, format="bgr24")
            video_frame.pts, video_frame.time_base = await self.next_timestamp()
            await asyncio.sleep(1 / self.frame_rate)
            return video_frame

    def __del__(self):
        self.capture.capture.stop()


class VideoStreamTrackCV2(VideoStreamTrack):
    def __init__(self, uri: str):
        super().__init__()

        self.uri = uri
        self.cv2_capture = cv2.VideoCapture(uri)
        self.frame_rate = self.cv2_capture.get(cv2.CAP_PROP_FPS) or 30

    async def recv(self):
        if not self.cv2_capture.isOpened():
            self.cv2_capture.open(self.cv2_capture.getBackendName(()))
            if not self.cv2_capture.isOpened():
                raise RuntimeError(f"Could not open video source: {self.uri!r}")

        ret, frame = self.cv2_capture.read()
        if not ret:
            raise RuntimeError(f"Could not read frame from video source: {self.uri!r}")

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts, video_frame.time_base = await self.next_timestamp()

        await asyncio.sleep(1 / self.frame_rate)
        return video_frame

    def __del__(self):
        if self.cv2_capture.isOpened():
            self.cv2_capture.release()


class AetherRTC:
    def __init__(self):
        self.pc = RTCPeerConnection()

    async def initiate_Offer(self):
        self.pc.addTrack(ScreenStreamTrack())

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
