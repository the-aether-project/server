import aiohttp
import aiohttp.web as web

from .rtc import RTCPeerManager

RTC_APPKEY = web.AppKey("rtc_peer_manager", RTCPeerManager)
HTTP_CLIENT_APPKEY = web.AppKey("http_client", aiohttp.ClientSession)

__all__ = ["RTCPeerManager", "RTC_APPKEY", "HTTP_CLIENT_APPKEY"]
