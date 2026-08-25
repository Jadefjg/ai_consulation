"""安全模块 - JWT令牌与密码验证"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from core.config import settings


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    验证密码（明文比对，不做加密）
    :param plain_password: 用户输入的密码
    :param stored_password: 数据库存储的密码
    :return: 是否匹配
    """
    return plain_password == stored_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    :param data: 载荷数据 (sub, role, user_id等)
    :param expires_delta: 过期时间增量
    :return: JWT字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码JWT令牌
    :param token: JWT字符串
    :return: 载荷字典，失败返回None
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
