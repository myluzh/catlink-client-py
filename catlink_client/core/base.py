#!/usr/bin/env python3
"""CATLINK 基础客户端：统一签名、登录、编码、错误与请求保护。"""

import logging
import os
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

import requests

from .errors import (
    CatLinkHTTPError,
    CatLinkProtocolError,
    CatLinkTransportError,
    CatlinkAPIError,
    DeviceControlBlocked,
    MissingParameter,
)
from .utils import (
    API_SERVERS,
    CONTROL_ENV,
    encrypt_password,
    is_write_authorized,
    new_noncestr,
    normalize_params,
    sign_params,
)

try:  # 生成物在首次生成前允许缺省，测试会校验最终存在
    from ..read_paths import READ_PATHS
except ImportError:  # pragma: no cover - bootstrap only
    READ_PATHS = frozenset()

try:
    from ..contract import DEVICE_ID_REQUIRED
except ImportError:  # pragma: no cover - bootstrap only
    DEVICE_ID_REQUIRED = frozenset()


logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30

HEADERS = {
    "language": "zh_CN",
    "User-Agent": "CATLINK/4.3.9",
    "app_version": "4.3.9",
    "system_version": "14",
}

ALLOWED_HOSTS = frozenset(urlsplit(url).hostname for url in API_SERVERS.values())
ALLOWED_METHODS = frozenset({"GET", "POST"})

# 认证类接口不涉及设备控制，未授权时仍可调用
AUTH_PATHS = frozenset({
    "api/login/password",
    "api/login/password/v2",
    "api/login/3rd",
    "api/login/loginWithSmsCode",
    "api/login/validate",
    "api/registerOrLogin",
    "api/sms/sendCommonSmsCode",
})

RC_TOKEN_EXPIRED = 1002


def _normalize_path(path: str) -> str:
    """统一成 ``api/token/...`` 形式，便于查白名单。

    查询串与 fragment 一律剥离，避免异常文本或白名单判断携带 token/sign。
    """
    value = (path or "").strip()
    if "?" in value or "#" in value:
        value = urlsplit(value).path
    if value.startswith("/"):
        value = value[1:]
    if not value.startswith("api/"):
        value = "api/" + value
    return value


def _bare_path(path: str) -> str:
    """去掉 ``api/`` 前缀，供拼接 base 使用。"""
    return _normalize_path(path)[4:]


def is_read_path(path: str) -> bool:
    """判断路径是否属于只读白名单。"""
    return _normalize_path(path) in READ_PATHS


def _normalize_method(method: str) -> str:
    if not isinstance(method, str):
        raise TypeError("method must be a str")
    value = method.strip().upper()
    if value not in ALLOWED_METHODS:
        raise ValueError(
            f"unsupported HTTP method: {method!r}; allowed {sorted(ALLOWED_METHODS)}"
        )
    return value


class CatLinkBaseClient:
    """CATLINK API 基础客户端。"""

    def __init__(
        self,
        phone: str,
        password: str,
        phone_iac: str = "86",
        region: str = "china",
        language: str = "zh_CN",
        session=None,
    ):
        """
        Args:
            phone: 手机号。
            password: 明文密码。
            phone_iac: 国家代码，默认 86。
            region: API 区域，可选 global/china/usa/singapore。
            language: 语言，默认 zh_CN。
            session: 可选 requests.Session 兼容对象，便于离线测试与复用。
        """
        self.phone = phone
        self.password = password
        self.phone_iac = phone_iac
        self.api_base = API_SERVERS.get(region, API_SERVERS["china"])
        self.language = language
        self.token: Optional[str] = None
        self.session = session if session is not None else requests.Session()
        self.last_return_code = None

    # ---------------- URL 与授权 ----------------
    def _api_url(self, api: str) -> str:
        """拼接 API URL，仅允许向官方 HTTPS API 主机发送请求。"""
        parts = urlsplit(api)
        url = api if parts.scheme or parts.netloc else (
            f"{self.api_base.rstrip('/')}/{api.lstrip('/')}"
        )
        target = urlsplit(url)
        if (
            target.scheme != "https"
            or target.hostname not in ALLOWED_HOSTS
            or target.username is not None
            or target.password is not None
            or target.port not in (None, 443)
        ):
            raise ValueError("CATLINK API URL must use an official HTTPS API host")
        return url

    def _build_url(self, path: str) -> str:
        return self._api_url(_bare_path(path))

    def _resolve_target(self, api: str):
        """返回 (url, 规范路径)；完整 URL 与相对路径都支持。"""
        if "://" in api or api.startswith("//"):
            url = self._api_url(api if "://" in api else "https:" + api)
            parts = urlsplit(url)
            # 完整 URL 的查询串/fragment 不进入请求，避免凭据出现在 URL 或日志。
            url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
            return url, _normalize_path(parts.path)
        norm = _normalize_path(api)
        return self._build_url(norm), norm

    def require_write(self, allow_write: Any, path: str = "") -> None:
        """写操作授权检查；失败时抛出 ``DeviceControlBlocked``。"""
        if not is_write_authorized(allow_write):
            raise DeviceControlBlocked(
                f"blocked write on {path or 'operation'}; "
                f"pass allow_write=True or set {CONTROL_ENV}=1"
            )

    # ---------------- 底层请求 ----------------
    def _prepare(
        self,
        params: Optional[Dict[str, Any]],
        files_entry: Any = None,
    ):
        """编码参数并签名；multipart 走独立分支。"""
        payload = normalize_params(params or {})
        payload["noncestr"] = new_noncestr()
        if self.token:
            payload["token"] = self.token
        payload["sign"] = sign_params(payload)

        if files_entry is None:
            return payload, None, None

        if not isinstance(files_entry, dict):
            raise TypeError("_files must be a mapping with data/filename")
        data = files_entry.get("data")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(
                "multipart data must be bytes/bytearray, got "
                f"{type(data).__name__}; open(path,'rb').read() is required"
            )
        filename = files_entry.get("filename") or "upload.bin"

        auth = {
            "noncestr": new_noncestr(),
        }
        if self.token:
            auth["token"] = self.token
        auth_sign = dict(payload)
        for key in ("noncestr", "token", "sign"):
            auth_sign.pop(key, None)
        auth_sign.update(auth)
        auth_sign["sign"] = sign_params(auth_sign)

        device_id = str(payload.get("deviceId", ""))
        boundary = "----CatlinkFormBoundary" + os.urandom(8).hex()
        parts = [
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: multipart/form-data\r\n\r\n"
            ).encode()
            + bytes(data)
            + b"\r\n",
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="deviceId"\r\n\r\n'
                f"{device_id}\r\n"
            ).encode(),
            (
                f"--{boundary}\r\n"
                f"deviceId: {device_id}\r\n\r\n\r\n"
            ).encode(),
        ]
        for key in ("noncestr", "token", "sign"):
            if auth_sign.get(key) not in (None, ""):
                parts.append(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                        f"{auth_sign[key]}\r\n"
                    ).encode()
                )
        body = b"".join(parts) + f"--{boundary}--\r\n".encode()
        return auth_sign, body, f"multipart/form-data; boundary={boundary}"

    def _perform(
        self,
        api: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        *,
        allow_write: Any = False,
        raise_on_error: bool = True,
        retry_auth: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        enforce_device_id: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        http_method = _normalize_method(method)
        url, norm = self._resolve_target(api)

        read_only = norm in READ_PATHS
        if not read_only and norm not in AUTH_PATHS:
            self.require_write(allow_write, norm)

        if enforce_device_id and norm in DEVICE_ID_REQUIRED:
            device_id = (params or {}).get("deviceId")
            if device_id is None or (isinstance(device_id, str) and device_id == ""):
                raise MissingParameter(
                    f"{norm} requires deviceId, got {device_id!r}"
                )

        raw = dict(params or {})
        files_entry = raw.pop("_files", None)
        if files_entry is not None and http_method != "POST":
            raise ValueError("_files is supported only for POST requests")

        payload, multipart_body, content_type = self._prepare(raw, files_entry)

        headers = dict(HEADERS)
        headers["language"] = self.language
        if self.token:
            headers["token"] = self.token
        if content_type:
            headers["Content-Type"] = content_type

        request_kwargs = dict(extra or {})
        request_kwargs.pop("allow_redirects", None)
        request_kwargs["allow_redirects"] = False
        request_kwargs["timeout"] = timeout
        request_kwargs["headers"] = headers
        if http_method == "GET":
            request_kwargs["params"] = payload
        else:
            request_kwargs["data"] = (
                multipart_body if multipart_body is not None else payload
            )

        try:
            response = self.session.request(http_method, url, **request_kwargs)
        except requests.RequestException as exc:
            raise CatLinkTransportError(type(exc).__name__, norm) from None

        if 300 <= response.status_code < 400:
            raise CatLinkHTTPError("redirect", norm, response.status_code)
        if response.status_code >= 400:
            raise CatLinkHTTPError("http", norm, response.status_code)

        try:
            body = response.json()
        except ValueError:
            raise CatLinkProtocolError("non-json response", norm) from None
        if not isinstance(body, dict):
            raise CatLinkProtocolError(f"{norm} response must be a JSON object", norm)

        return_code = body.get("returnCode")
        self.last_return_code = return_code
        if (
            isinstance(return_code, int)
            and not isinstance(return_code, bool)
            and return_code == 0
        ):
            return body
        if return_code is None:
            raise CatLinkProtocolError("missing-returnCode", norm)
        if isinstance(return_code, bool) or not isinstance(return_code, int):
            raise CatLinkProtocolError(
                f"invalid-returnCode-type:{type(return_code).__name__}", norm
            )

        if return_code == RC_TOKEN_EXPIRED and retry_auth and read_only:
            if self.login():
                return self._perform(
                    api,
                    params,
                    http_method,
                    allow_write=allow_write,
                    raise_on_error=raise_on_error,
                    retry_auth=False,
                    timeout=timeout,
                    enforce_device_id=enforce_device_id,
                    extra=extra,
                )

        if raise_on_error:
            raise CatlinkAPIError(norm, return_code, body.get("msg"))
        return body

    def call(
        self,
        api: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        *,
        allow_write: Any = False,
        raise_on_error: bool = True,
        retry_auth: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """统一入口：默认 POST，业务错误抛 ``CatlinkAPIError``。"""
        return self._perform(
            api,
            params,
            method,
            allow_write=allow_write,
            raise_on_error=raise_on_error,
            retry_auth=retry_auth,
            timeout=timeout,
        )

    def call_raw(
        self,
        api: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        **kwargs,
    ) -> Dict[str, Any]:
        """不因业务错误抛异常，返回完整响应信封。"""
        kwargs["raise_on_error"] = False
        return self.call(api, params, method, **kwargs)

    def _request(
        self,
        api: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        *,
        allow_write: Any = False,
        raise_on_error: bool = False,
        retry_auth: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        enforce_device_id: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """旧入口兼容层：默认 GET，业务错误返回信封。

        协议层与传输层异常仍统一抛错；新代码建议使用 :meth:`call`。
        """
        return self._perform(
            api,
            params,
            method,
            allow_write=allow_write,
            raise_on_error=raise_on_error,
            retry_auth=retry_auth,
            timeout=timeout,
            enforce_device_id=enforce_device_id,
            extra=kwargs,
        )

    # ---------------- 认证 ----------------
    def login(self) -> bool:
        """登录获取 token；成功判定与 4.3.9 客户端一致。"""
        params = {
            "platform": "ANDROID",
            "internationalCode": self.phone_iac,
            "mobile": self.phone,
            "password": encrypt_password(self.password),
        }
        old_token = self.token
        self.token = None
        try:
            body = self._request(
                "login/password",
                params,
                "POST",
                raise_on_error=False,
                retry_auth=False,
            )
            if body.get("returnCode") != 0:
                self.token = old_token
                logger.warning(
                    "CATLINK login failed: returnCode=%s", body.get("returnCode")
                )
                return False
            data = body.get("data")
            if not isinstance(data, dict):
                raise CatLinkProtocolError(
                    f"invalid-login-data:{type(data).__name__}", "api/login/password"
                )
            token = data.get("token")
            if not isinstance(token, str) or not token:
                self.token = old_token
                logger.warning("CATLINK login failed: token is absent")
                return False
            self.token = token
            logger.info("CATLINK login succeeded")
            return True
        except Exception:
            self.token = old_token
            raise

    # ---------------- 通用查询 ----------------
    def get_device_detail(self, device_id: str) -> Dict[str, Any]:
        """获取设备详情（通用接口，适用于未映射专用 client 的设备）。"""
        return self._request("token/device/info", {"deviceId": device_id})

    @staticmethod
    def _devices_from_data(data: Any) -> list:
        """兼容直接列表、devices 列表及 devices.records 分页结构。"""
        if isinstance(data, dict):
            data = data.get("devices")
            if isinstance(data, dict):
                data = data.get("records")
        return data if isinstance(data, list) else []

    def get_devices(self) -> list:
        """查询设备，优先使用覆盖新设备的 sortedListV2 接口。

        Returns:
            设备字典列表，保留 deviceName、deviceType、onlineStatus 等原字段。
            V2 返回空列表时依次兼容两个旧接口；旧接口可能不包含新设备。
            本方法只读，无需 allow_write 授权。
        """
        if not self.token and not self.login():
            return []

        for path in (
            "token/device/union/sortedListV2",
            "token/device/list",
            "token/device/union/list/sorted",
        ):
            resp = self._request(path, {"type": "NONE"}, "GET")
            devices = self._devices_from_data(resp.get("data"))
            if devices:
                return devices
        return []

    def is_read_path(self, path: str) -> bool:
        """实例方法形式的只读路径判断。"""
        return is_read_path(path)

    # ---------------- 统一操作入口 ----------------
    @property
    def operations(self):
        """399 条操作的统一派发器。"""
        from ..operations import CatLinkOperations

        return CatLinkOperations(self)

    @property
    def api(self):
        """设备查询和控制的便捷方法集合。"""
        from ..device_api import CatLinkDeviceAPI

        return CatLinkDeviceAPI(self)

    def dispatch(self, slug: str, **params) -> Dict[str, Any]:
        """按操作 slug 派发；参数校验与 defaults/derived 由派发器处理。"""
        return self.operations.call(slug, **params)
