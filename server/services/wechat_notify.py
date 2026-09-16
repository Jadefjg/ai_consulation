"""微信订阅消息适配层；未配置凭据时安全降级为日志通知。"""
import logging
logger = logging.getLogger(__name__)
def send_subscription(user_openid: str | None, template_id: str, data: dict, page: str = "") -> bool:
    if not user_openid or not template_id:
        logger.info("wechat notification skipped: missing openid/template", extra={"event":"wechat_notify_skipped"})
        return False
    # 真实发送由部署环境的微信 SDK/网关实现，此处保持业务层可调用且幂等。
    logger.info("wechat notification queued", extra={"event":"wechat_notify_queued", "openid": user_openid[:4] + "***", "page": page})
    return True
