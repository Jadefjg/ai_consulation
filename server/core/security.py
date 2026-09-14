"""安全模块 - JWT令牌与密码哈希"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from core.config import settings

_HASH_PREFIX = "pbkdf2_sha256"
_HASH_ROUNDS = 120_000


def hash_password(plain_password: str) -> str:
    """
    使用 PBKDF2-SHA256 哈希密码
    :param plain_password: 明文密码
    :return: 存储用哈希串
    """
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        _HASH_ROUNDS,
    ).hex()
    return f"{_HASH_PREFIX}${salt}${digest}"


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    验证密码（兼容历史明文，校验通过后可在业务层升级为哈希）
    :param plain_password: 用户输入的密码
    :param stored_password: 数据库存储的密码或哈希
    :return: 是否匹配
    """
    if not plain_password or not stored_password:
        return False
    if stored_password.startswith(f"{_HASH_PREFIX}$"):
        try:
            _, salt, digest = stored_password.split("$", 2)
        except ValueError:
            return False
        check = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            _HASH_ROUNDS,
        ).hex()
        return hmac.compare_digest(check, digest)
    # 兼容旧版明文存储
    return hmac.compare_digest(plain_password, stored_password)


def is_password_hashed(stored_password: str) -> bool:
    """判断库中密码是否已是哈希格式"""
    return bool(stored_password) and stored_password.startswith(f"{_HASH_PREFIX}$")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    :param data: 载荷数据 (sub, role, user_id等)
    :param expires_delta: 过期时间增量
    :return: JWT字符串
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
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
