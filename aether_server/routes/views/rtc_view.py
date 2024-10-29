from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import cv2
from av import VideoFrame

import asyncio


class VideoStreamTrackFromFile(VideoStreamTrack):
    def __init__(self, file_path):
        super().__init__()
        self.cap = cv2.VideoCapture(file_path)
        self.frame_rate = self.cap.get(cv2.CAP_PROP_FPS) or 30

    async def recv(self):
        if not self.cap.isOpened():
            print("Capture  source not open. Retrying.")
            self.cap.open(self.cap.getBackendName(()))
            if not self.cap.isOpened():
                print("Failed")
                raise RuntimeError("Video capture source not opened")

        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read video source")

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts, video_frame.time_base = await self.next_timestamp()

        await asyncio.sleep(1 / self.frame_rate)
        return video_frame

    def __del__(self):
        if self.cap.isOpened():
            self.cap.release()


class AetherRtc:
    def __init__(self):
        self.pc = RTCPeerConnection()

    async def initiate_Offer(self):
        video_track = VideoStreamTrackFromFile(
            # "path to the video"
        )
        self.pc.addTrack(video_track)

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        return {
            "type": self.pc.localDescription.type,
            "sdp": self.pc.localDescription.sdp,
        }

    async def take_answer(self, answer_data):
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        await self.pc.setRemoteDescription(answer)
