#!/usr/bin/env python3
"""CATLINK FEEDER 普通喂食器设备"""

from typing import Dict, Any

from ..core.base import CatLinkBaseClient


class FeederClient:
    """FEEDER 普通喂食器客户端"""

    def __init__(self, base_client: CatLinkBaseClient):
        """
        初始化喂食器客户端

        Args:
            base_client: 基础客户端实例
        """
        self.client = base_client

    def get_detail(self, device_id: str) -> Dict[str, Any]:
        """
        获取喂食器设备详情

        Args:
            device_id: 设备 ID

        Returns:
            设备详情
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/feeder/detail",
            {"deviceId": device_id}
        )

        return (resp.get("data") or {}).get("deviceInfo") or {}

    def get_logs_top5(self, device_id: str) -> Dict[str, Any]:
        """
        获取喂食器记录 Top5

        Args:
            device_id: 设备 ID

        Returns:
            记录
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/feeder/stats/log/top5",
            {"deviceId": device_id}
        )

        return resp.get("data") or {}

    def food_out(self, device_id: str, portions: int = 1, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        出粮

        Args:
            device_id: 设备 ID
            portions: 份数（1-10）

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/feeder/foodOut",
            {
                "deviceId": device_id,
                "footOutNum": portions
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp
