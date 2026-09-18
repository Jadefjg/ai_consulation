"""微信订阅消息适配层。未配置凭据时安全降级；配置后调用官方 API。"""
import logging
import time
import requests
from core.config import settings
logger = logging.getLogger(__name__)
_token_cache = {"value": "", "expires_at": 0.0}

def _access_token():
    if _token_cache["value"] and _token_cache["expires_at"] > time.time() + 30:
        return _token_cache["value"]
    if not settings.wechat_mini_appid or not settings.wechat_mini_secret:
        return None
    try:
        r = requests.get("https://api.weixin.qq.com/cgi-bin/token", params={"grant_type":"client_credential", "appid":settings.wechat_mini_appid, "secret":settings.wechat_mini_secret}, timeout=settings.wechat_api_timeout_seconds)
        payload = r.json()
        if payload.get("access_token"):
            _token_cache.update(value=payload["access_token"], expires_at=time.time()+int(payload.get("expires_in", 7200)))
            return _token_cache["value"]
    except Exception:
        logger.exception("wechat access token request failed")
    return None

def send_subscription(user_openid: str | None, template_id: str, data: dict, page: str = "") -> bool:
    if not user_openid or not template_id:
        logger.info("wechat notification skipped: missing openid/template", extra={"event":"wechat_notify_skipped"})
        return False
    token = _access_token()
    if not token:
        logger.info("wechat notification skipped: credentials unavailable", extra={"event":"wechat_notify_skipped"})
        return False
    try:
        r = requests.post("https://api.weixin.qq.com/cgi-bin/message/subscribe/send", params={"access_token": token}, json={"touser": user_openid, "template_id": template_id, "page": page, "data": data}, timeout=settings.wechat_api_timeout_seconds)
        payload = r.json()
        ok = payload.get("errcode", 0) == 0
        if not ok: logger.warning("wechat subscription rejected: %s", payload)
        return ok
    except Exception:
        logger.exception("wechat subscription request failed")
        return False
