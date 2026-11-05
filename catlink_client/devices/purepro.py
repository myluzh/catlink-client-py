#!/usr/bin/env python3
"""CATLINK PUREPRO 水碗设备"""

from typing import Dict, Any

from ..core.base import CatLinkBaseClient


class PureProClient:
    """PUREPRO 水碗客户端"""

    # 出水模式常量
    RUN_MODES = {
        "CONTINUOUS_SPRING": "continuous",  # 持续涌泉
        "INTERMITTENT_SPRING": "intermittent",  # 间接涌泉
        "INDUCTION_SPRING": "induction",  # 智能涌泉
    }

    def __init__(self, base_client: CatLinkBaseClient):
        """
        初始化水碗客户端

        Args:
            base_client: 基础客户端实例
        """
        self.client = base_client

    def get_detail(self, device_id: str) -> Dict[str, Any]:
        """
        获取水碗设备详情

        Args:
            device_id: 设备 ID

        Returns:
            设备详情
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/purepro/detail",
            {"deviceId": device_id}
        )

        data = resp.get("data") or {}
        # PurePro API 可能直接返回数据，或者在 deviceInfo 中
        return data.get("deviceInfo") or data

    def get_logs_top5(self, device_id: str) -> Dict[str, Any]:
        """
        获取水碗记录 Top5

        Args:
            device_id: 设备 ID

        Returns:
            记录
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/purepro/stats/log/top5",
            {"deviceId": device_id}
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
        获取水碗历史记录（分页）

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
            "token/device/purepro/stats/log/list",
            {
                "deviceId": device_id,
                "date": date,
                "pageNumber": page_number,
                "pageSize": page_size
            }
        )

        return resp.get("data") or {}

    def set_run_mode(self, device_id: str, mode: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        设置水碗出水模式

        Args:
            device_id: 设备 ID
            mode: 出水模式
                - "CONTINUOUS_SPRING" 或 "continuous" - 持续涌泉
                - "INTERMITTENT_SPRING" 或 "intermittent" - 间接涌泉
                - "INDUCTION_SPRING" 或 "induction" - 智能涌泉

        Returns:
            响应结果
        """
        # 支持中英文模式名称
        mode_map = {
            "continuous": "CONTINUOUS_SPRING",
            "intermittent": "INTERMITTENT_SPRING",
            "induction": "INDUCTION_SPRING",
            "持续涌泉": "CONTINUOUS_SPRING",
            "间接涌泉": "INTERMITTENT_SPRING",
            "智能涌泉": "INDUCTION_SPRING",
        }

        # 如果直接传入的是模式常量，直接使用
        if mode in self.RUN_MODES:
            run_mode = mode
        else:
            run_mode = mode_map.get(mode)
            if run_mode is None:
                return {"returnCode": -1, "returnMsg": f"Invalid mode: {mode}"}

        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/device/purepro/runMode",
            {
                "deviceId": device_id,
                "runMode": run_mode
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp
