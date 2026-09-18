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
_DEVTOOLS_MOCK_OPENID = "devtools_mock_openid"
_DEVTOOLS_MOCK_CODES = {
    "the code is a mock one",
    "mock",
    "mock_code",
}


def _normalize_code(code: str) -> str:
    return (code or "").strip()


def _mock_openid(code: str) -> str | None:
    """识别微信开发者工具 / 本地模拟登录码，无法拿去调微信官方接口。"""
    if code.startswith("dev_"):
        openid = code[4:].strip()
        if len(openid) < 8:
            raise HTTPException(status_code=400, detail="开发登录 openid 至少 8 位")
        return openid
    if code.lower() in _DEVTOOLS_MOCK_CODES:
        return _DEVTOOLS_MOCK_OPENID
    return None


def _allow_mock_login() -> bool:
    if settings.wechat_dev_login:
        return True
    # 未配置密钥时官方 code2session 必然失败，开发者工具 mock 码只能走本地账户。
    return not settings.wechat_mini_appid or not settings.wechat_mini_secret


def jscode2session(code: str) -> tuple[str, str | None]:
    """
    用 wx.login code 换 openid / unionid。
    开发者工具游客/未登录时会给出 mock code；未配置 AppSecret 时映射为稳定的演示 openid。
    """
    normalized = _normalize_code(code)
    if not normalized:
        raise HTTPException(status_code=400, detail="缺少微信登录 code")

    mock_openid = _mock_openid(normalized)
    if mock_openid:
        if _allow_mock_login():
            logger.info("wechat mock login accepted", extra={"event": "wechat_login_mock"})
            return mock_openid, None
        raise HTTPException(status_code=401, detail="当前为模拟登录码，请在已登录的开发者工具或真机上重试")

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
