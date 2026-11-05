#!/usr/bin/env python3
"""CATLINK SCOOPER 猫砂盆设备"""

from typing import Dict, Any

from ..core.base import CatLinkBaseClient


class ScooperClient:
    """SCOOPER 猫砂盆客户端"""

    MODES = {"00": "auto", "01": "manual", "02": "time", "03": "empty"}
    ACTIONS = {"00": "pause", "01": "start"}

    def __init__(self, base_client: CatLinkBaseClient):
        """
        初始化猫砂盆客户端

        Args:
            base_client: 基础客户端实例
        """
        self.client = base_client

    def get_detail(self, device_id: str) -> Dict[str, Any]:
        """
        获取猫砂盆设备详情（使用通用 API）

        Args:
            device_id: 设备 ID

        Returns:
            设备详情
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/info",
            {"deviceId": device_id}
        )

        return (resp.get("data") or {}).get("deviceInfo") or {}

    def get_logs_top5(self, device_id: str) -> Dict[str, Any]:
        """
        获取猫砂盆记录 Top5

        Args:
            device_id: 设备 ID

        Returns:
            记录
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/scooper/stats/log/top5",
            {"deviceId": device_id}
        )

        return resp.get("data") or {}

    def change_mode(self, device_id: str, mode: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """切换 SCOOPER 工作模式。

        Args:
            device_id: 设备 ID。
            mode: auto/manual/time/empty，或对应编码 00/01/02/03。

        Returns:
            完整 API 响应；无效模式返回 returnCode=-1，登录失败返回空字典。
        """
        code = mode if mode in self.MODES else next(
            (key for key, value in self.MODES.items() if value == mode), None
        )
        if code is None:
            return {"returnCode": -1, "returnMsg": f"Invalid mode: {mode}"}
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}
        return self.client._request(
            "token/device/changeMode",
            {"deviceId": device_id, "workModel": code},
            method="POST",
            allow_write=allow_write,
        )

    def set_action(self, device_id: str, action: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """启动或暂停 SCOOPER。

        Args:
            device_id: 设备 ID。
            action: start/pause，或对应编码 01/00。

        Returns:
            完整 API 响应；无效动作返回 returnCode=-1，登录失败返回空字典。
        """
        code = action if action in self.ACTIONS else next(
            (key for key, value in self.ACTIONS.items() if value == action), None
        )
        if code is None:
            return {"returnCode": -1, "returnMsg": f"Invalid action: {action}"}
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}
        return self.client._request(
            "token/device/actionCmd",
            {"deviceId": device_id, "cmd": code},
            method="POST",
            allow_write=allow_write,
        )
