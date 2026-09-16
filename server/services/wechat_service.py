"""微信小程序登录：code2session。"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from fastapi import HTTPException

from core.config import settings

logger = logging.getLogger(__name__)

_JSCODE2SESSION = "https://api.weixin.qq.com/sns/jscode2session"


def jscode2session(code: str) -> tuple[str, str | None]:
    """
    用 wx.login code 换 openid / unionid。
    开发环境可传 dev_ 前缀的 code，跳过真实微信接口。
    """
    normalized = (code or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="缺少微信登录 code")

    if settings.wechat_dev_login and normalized.startswith("dev_"):
        openid = normalized[4:].strip()
        if len(openid) < 8:
            raise HTTPException(status_code=400, detail="开发登录 openid 至少 8 位")
        return openid, None

    if not settings.wechat_mini_appid or not settings.wechat_mini_secret:
        raise HTTPException(status_code=503, detail="未配置微信小程序 AppID/Secret")

    query = urllib.parse.urlencode({
        "appid": settings.wechat_mini_appid,
        "secret": settings.wechat_mini_secret,
        "js_code": normalized,
        "grant_type": "authorization_code",
    })
    try:
        with urllib.request.urlopen(f"{_JSCODE2SESSION}?{query}", timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("wechat jscode2session failed: %s", exc, extra={"event": "wechat_login_upstream"})
        raise HTTPException(status_code=502, detail="微信登录服务暂时不可用") from exc

    errcode = payload.get("errcode") or 0
    if errcode:
        logger.warning(
            "wechat jscode2session rejected: errcode=%s",
            errcode,
            extra={"event": "wechat_login_rejected"},
        )
        raise HTTPException(status_code=401, detail="微信登录失败，请重试")

    openid = payload.get("openid")
    if not openid:
        raise HTTPException(status_code=401, detail="微信登录失败，请重试")
    return str(openid), payload.get("unionid")
