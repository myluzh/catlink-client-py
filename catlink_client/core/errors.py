#!/usr/bin/env python3
"""CATLINK 客户端统一错误类型。

设计目标：
* 所有入口共享同一套错误分类；
* 异常文本只保留状态码、错误类别与脱敏路径，不带 token、sign 或完整查询串；
* 旧客户端依赖的 ``requests.HTTPError`` / ``ValueError`` 捕获方式仍然有效。
"""
from __future__ import annotations

import requests


class CatLinkError(RuntimeError):
    """客户端所有错误的基类。"""


class CatLinkTransportError(CatLinkError, requests.RequestException):
    """网络、HTTP 或协议层失败（消息中不含查询串）。

    Args:
        reason: 错误类别，如 ``Timeout``、``http-404``。
        path: 脱敏后的接口路径，如 ``api/token/device/info``。
        status: HTTP 状态码（如可获得）。
    """

    def __init__(self, reason: str, path: str = "", status=None):
        self.reason = str(reason)
        self.path = path
        self.status = status
        self.response = None
        text = f"transport {self.reason}"
        if status is not None:
            text += f" status={status}"
        if path:
            text += f" on {path}"
        CatLinkError.__init__(self, text)


class CatLinkHTTPError(CatLinkTransportError, requests.HTTPError):
    """HTTP 状态异常；同时是 ``requests.HTTPError`` 子类。"""


class CatLinkProtocolError(CatLinkTransportError, ValueError):
    """响应信封不符合协议；同时是 ``ValueError`` 子类。"""


class CatlinkAPIError(CatLinkError):
    """服务端业务失败（returnCode != 0）。"""

    def __init__(self, path: str, return_code, msg=None):
        self.path = path
        self.return_code = return_code
        self.msg = msg
        # 服务端 msg 可能回显 token、sign 或其他敏感内容，只保留结构化属性，
        # 不拼进异常文本（异常日志通常会被采集）。
        super().__init__(f"returnCode={return_code} on {path}")


class DeviceControlBlocked(CatLinkError):
    """未显式授权时拒绝下发设备控制指令。"""


class MissingParameter(ValueError):
    """缺少必填参数。"""


class UnknownParameter(ValueError):
    """传入了目录中不存在的参数。"""


class DisabledOperation(CatLinkError):
    """服务端不存在的端点，派发器直接拒绝并给出替代路径。"""


class UnconfirmedContract(CatLinkError):
    """参数契约未确认（仅有接口声明，缺少调用点证据）。"""


# 来源项目命名兼容别名
CatlinkTransportError = CatLinkTransportError
CatlinkProtocolError = CatLinkProtocolError
