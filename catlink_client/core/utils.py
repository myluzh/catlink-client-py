#!/usr/bin/env python3
"""CATLINK 客户端工具函数：协议常量、签名、编码与加密。"""

import base64
import hashlib
import os
import time
from typing import Any, Dict
from urllib.parse import unquote_plus

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

# API 配置
API_SERVERS = {
    "global": "https://app.catlinks.cn/api/",
    "china": "https://app-sh.catlinks.cn/api/",
    "usa": "https://app-usa.catlinks.cn/api/",
    "singapore": "https://app-sgp.catlinks.cn/api/",
}

# CATLINK 4.3.9 签名密钥
SIGN_KEY = "G3fLpdb1dO1yTwcAMv2HYbp1nPLeb75sjusJmy2YSyp5D2oXzp4I82SGWcB8dwBK"

RSA_PUBLIC_KEY = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCCA9I+iEl2AI8dnhdwwxPxHVK8iNAt6aTq6UhNsLsguWS5qtbLnuGz2RQdfNS"
    "aKSU2B6D/vE2gb1fM6f1A5cKndqF/riWGWn1EfL3FFQZduOTxoA0RTQzhrTa5LHcJ/an/NuHUwShwIOij0Mf4g8faTe4FT7/HdA"
    "oK7uW0cG9mZwIDAQAB"
)

# 绑定类接口 authPwd 的 AES/CBC 参数
CAM_AES_KEY = "I4iRiHm1s23ERWiu"
CAM_AES_IV = "2ROHQMVxPJ61XUKQ"

# App 拦截器仅保留这两个字段的空字符串
KEEP_EMPTY = frozenset({"faceIdList", "fileIdList"})

# 可通过环境变量显式开启真实设备控制
CONTROL_ENV = "CATLINK_ALLOW_DEVICE_CONTROL"


def _hash_password(password: str) -> str:
    """密码哈希预处理（MD5 小写 → SHA1 大写）。"""
    md5_hash = hashlib.md5(password.encode()).hexdigest().lower()
    return hashlib.sha1(md5_hash.encode()).hexdigest().upper()


def encrypt_password(password: str) -> str:
    """MD5 → SHA1 → RSA/PKCS1v15 → Base64。"""
    sha1_hash = _hash_password(password)
    pub_key = serialization.load_der_public_key(base64.b64decode(RSA_PUBLIC_KEY))
    encrypted = pub_key.encrypt(sha1_hash.encode(), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode()


def sign_value(key: str, value: Any) -> Any:
    """签名前的单字段变换。

    App SignUtils 只对 ``timezoneId`` 做一次 URLDecode，再参与排序拼接；
    Java ``URLDecoder.decode`` 语义等价于 ``unquote_plus``（'+' → 空格，%XX 解码）。
    """
    if key == "timezoneId":
        return unquote_plus(str(value))
    return value


def sign_params(params: Dict[str, Any]) -> str:
    """按 key 排序拼接，追加 ``&key=<SIGN_KEY>``，MD5 后转大写。"""
    raw = "&".join(f"{k}={sign_value(k, params[k])}" for k in sorted(params))
    return hashlib.md5((raw + f"&key={SIGN_KEY}").encode()).hexdigest().upper()


def normalize_value(value: Any) -> Any:
    """复现 App RequestParams 的值编码。

    * ``bool`` → ``"true"`` / ``"false"``（String.valueOf 小写）
    * ``list`` / ``tuple`` → 逗号分隔字符串
    """
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (list, tuple)):
        return ",".join(str(item) for item in value)
    return value


def normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """过滤 None、空字符串、旧 sign，并统一编码值。

    ``faceIdList`` / ``fileIdList`` 是 App 明确保留空串的两个例外。
    """
    normalized = {}
    for key, value in (params or {}).items():
        if value is None or key == "sign":
            continue
        normalized[key] = normalize_value(value)
    return {
        key: value
        for key, value in normalized.items()
        if not (isinstance(value, str) and value == "" and key not in KEEP_EMPTY)
    }


def new_noncestr() -> str:
    """毫秒时间戳字符串（App 以 String 形式写入表单并参与签名）。"""
    return str(int(time.time() * 1000))


def is_write_authorized(allow_write: Any) -> bool:
    """严格布尔判断：只接受 ``True`` 或环境变量 ``CATLINK_ALLOW_DEVICE_CONTROL=1``。"""
    if allow_write is True:
        return True
    if allow_write is False or allow_write is None:
        return os.environ.get(CONTROL_ENV) == "1"
    raise TypeError(
        f"allow_write must be bool, got {type(allow_write).__name__}: {allow_write!r}"
    )


def camera_auth_pwd(plain: str) -> str:
    """绑定类接口 authPwd：明文 → AES/CBC/PKCS7 → 大写十六进制。

    与 App ``AESUtils.cameraAesEncrypt`` 一致；空明文输入拒绝。
    """
    from cryptography.hazmat.primitives import padding as sym_padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    if not plain:
        raise ValueError("authPwd plaintext is empty")
    padder = sym_padding.PKCS7(128).padder()
    data = padder.update(plain.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(
        algorithms.AES(CAM_AES_KEY.encode("utf-8")),
        modes.CBC(CAM_AES_IV.encode("utf-8")),
    ).encryptor()
    return (encryptor.update(data) + encryptor.finalize()).hex().upper()


def pin_sha256(pin: str) -> str:
    """安全锁 PIN → 小写十六进制 SHA-256（App RSAUtils.sha256）。"""
    return hashlib.sha256(str(pin).encode("utf-8")).hexdigest()
