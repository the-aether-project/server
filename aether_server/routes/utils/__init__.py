import aiohttp.web as web

from .rtc import RTCPeerManager

RTC_APPKEY = web.AppKey("rtc_peer_manager", RTCPeerManager)


__all__ = ["RTCPeerManager", "RTC_APPKEY"]
