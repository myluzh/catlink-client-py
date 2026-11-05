#!/usr/bin/env python3
"""CATLINK FEEDER_PRO 喂食器设备"""

from typing import Dict, Any

from ..core.base import CatLinkBaseClient


class FeederProClient:
    """FEEDER_PRO 喂食器客户端"""

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
            "token/device/feederpro/detail",
            {"deviceId": device_id}
        )

        return resp.get("data") or {}

    def get_logs_top5(self, device_id: str) -> Dict[str, Any]:
        """
        获取喂食器出粮记录 Top5

        Args:
            device_id: 设备 ID

        Returns:
            出粮记录
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/feederpro/stats/log/top5",
            {"deviceId": device_id}
        )

        return resp.get("data") or {}

    def get_consumable_list(self, device_id: str) -> Dict[str, Any]:
        """
        获取喂食器耗材列表

        Args:
            device_id: 设备 ID

        Returns:
            耗材列表
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/union/consumableListForOne",
            {"deviceId": device_id, "deviceType": "FEEDER_PRO"}
        )

        return resp.get("data") or {}

    def get_logs_list(
        self,
        device_id: str,
        date: str,
        page_number: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取喂食器历史记录（分页）

        Args:
            device_id: 设备 ID
            date: 日期，格式 "YYYY-MM-DD"
            page_number: 页码，默认 1
            page_size: 每页数量，默认 20

        Returns:
            历史记录
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/feederpro/stats/log/list",
            {
                "deviceId": device_id,
                "date": date,
                "pageNumber": page_number,
                "pageSize": page_size
            }
        )

        return resp.get("data") or {}

    def food_out(self, device_id: str, portions: int = 1, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        喂食器 Pro 出粮（使用 v2 新接口）

        Args:
            device_id: 设备 ID
            portions: 出粮份数，1-5份，默认1份

        Returns:
            响应结果
        """
        # 验证份数范围
        if not 1 <= portions <= 5:
            return {"returnCode": -1, "returnMsg": "portions must be between 1 and 5"}

        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/feederpro/v2/foodOut",
            {
                "deviceId": device_id,
                "foodOutNum": portions
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp
