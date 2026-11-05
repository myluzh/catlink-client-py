#!/usr/bin/env python3
"""CATLINK VISUAL_PRO_ULTRA (Scooper Pro Ultra) 猫砂盆设备"""

from datetime import date
from typing import Dict, Any, List

from ..core.base import CatLinkBaseClient


class ScooperProUltraClient:
    """VISUAL_PRO_ULTRA (Scooper Pro Ultra) 猫砂盆客户端

    这是 Scooper Pro Ultra 高级版猫砂盆，提供有限的 API 支持
    """

    def __init__(self, base_client: CatLinkBaseClient):
        """
        初始化猫砂盆客户端

        Args:
            base_client: 基础客户端实例
        """
        self.client = base_client

    def get_detail(self, device_id: str) -> Dict[str, Any]:
        """
        获取猫砂盆设备详情（使用 briefInfo API）

        Args:
            device_id: 设备 ID

        Returns:
            设备详情
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/visualScooper/briefInfo",
            {"deviceId": device_id}
        )

        data = (resp.get("data") or {})
        # 可能直接返回数据，或在 deviceInfo 中
        return data.get("deviceInfo") or data

    def get_logs_top5(self, device_id: str) -> Dict[str, Any]:
        """
        获取猫砂盆记录 Top5

        注意：此设备使用 timeline/v2 API，返回格式可能与其他设备不同

        Args:
            device_id: 设备 ID

        Returns:
            记录
        """
        if not self.client.token and not self.client.login():
            return {}

        # 使用今天的日期获取日志
        today = date.today().isoformat()

        resp = self.client._request(
            "token/litterbox/stats/log/timeline/v2",
            {
                "deviceId": device_id,
                "date": today,
                "pageNumber": 1,
                "pageSize": 5,
                "type": 0,
                "subType": 0
            }
        )

        return resp.get("data") or {}

    def get_logs_timeline(
        self,
        device_id: str,
        date: str,
        page_number: int = 1,
        page_size: int = 20,
        log_type: int = 0,
        sub_type: int = 0
    ) -> Dict[str, Any]:
        """
        获取猫砂盆时间线日志（分页）

        Args:
            device_id: 设备 ID
            date: 日期，格式 "YYYY-MM-DD"
            page_number: 页码，默认 1
            page_size: 每页数量，默认 20
            log_type: 日志类型，默认 0
            sub_type: 子类型，默认 0

        Returns:
            时间线日志数据
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/stats/log/timeline/v2",
            {
                "deviceId": device_id,
                "date": date,
                "pageNumber": page_number,
                "pageSize": page_size,
                "type": log_type,
                "subType": sub_type
            }
        )

        return resp.get("data") or {}

    def get_logs_list(
        self,
        device_id: str,
        date: str,
        page_number: int = 1,
        page_size: int = 20
    ) -> List:
        """
        获取猫砂盆历史记录列表（分页）

        Args:
            device_id: 设备 ID
            date: 日期，格式 "YYYY-MM-DD"
            page_number: 页码，默认 1
            page_size: 每页数量，默认 20

        Returns:
            记录列表
        """
        result = self.get_logs_timeline(
            device_id=device_id,
            date=date,
            page_number=page_number,
            page_size=page_size
        )

        # 从返回数据中提取 records
        records = result.get("records") or []
        return records
