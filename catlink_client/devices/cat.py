#!/usr/bin/env python3
"""CATLINK 猫咪数据"""

from typing import Optional, Dict, Any, List

from ..core.base import CatLinkBaseClient


class CatClient:
    """猫咪数据客户端"""

    def __init__(self, base_client: CatLinkBaseClient):
        """
        初始化猫咪客户端

        Args:
            base_client: 基础客户端实例
        """
        self.client = base_client

    def get_list(self, timezone_id: Optional[str] = None) -> List:
        """
        获取猫咪列表

        Args:
            timezone_id: 时区 ID，如 "Asia/Shanghai"

        Returns:
            猫咪列表
        """
        if not self.client.token and not self.client.login():
            return []

        params = {}
        if timezone_id:
            params["timezoneId"] = timezone_id

        resp = self.client._request("token/pet/health/v3/cats", params)

        return (resp.get("data") or {}).get("cats") or []

    def get_summary(
        self,
        pet_id: str,
        date: str,
        timezone_id: Optional[str] = None,
        sport: int = 1
    ) -> Dict[str, Any]:
        """
        获取猫咪健康摘要

        Args:
            pet_id: 猫咪 ID
            date: 日期，格式 "YYYY-MM-DD"
            timezone_id: 时区 ID
            sport: 是否包含运动数据

        Returns:
            健康摘要数据
        """
        if not self.client.token and not self.client.login():
            return {}

        params = {
            "petId": pet_id,
            "date": date,
            "sport": sport,
        }
        if timezone_id:
            params["timezoneId"] = timezone_id

        resp = self.client._request("token/pet/health/v3/summarySimple", params)

        return resp.get("data") or {}

    def get_diet_chart_intake(
        self,
        cat_id: str,
        timezone_id: str,
        chart_type: str = "WEEK",
        cursor: int = 0
    ) -> Dict[str, Any]:
        """
        获取猫咪饮食摄入图表数据（进食量）

        Args:
            cat_id: 猫咪 ID
            timezone_id: 时区 ID，如 "Asia/Shanghai"
            chart_type: 图表类型，WEEK（周）/MONTH（月）/YEAR（年）
            cursor: 游标，用于分页，默认 0

        Returns:
            饮食摄入图表数据
        """
        if not self.client.token and not self.client.login():
            return {}

        params = {
            "catId": cat_id,
            "timezoneId": timezone_id,
            "type": chart_type,
            "cursor": cursor
        }

        resp = self.client._request("token/pet/health/v2/diet/chart/intake", params)

        return resp.get("data") or {}

    def get_diet_chart_duration(
        self,
        cat_id: str,
        timezone_id: str,
        chart_type: str = "WEEK",
        cursor: int = 0
    ) -> Dict[str, Any]:
        """
        获取猫咪饮食时长图表数据（进食时长）

        Args:
            cat_id: 猫咪 ID
            timezone_id: 时区 ID，如 "Asia/Shanghai"
            chart_type: 图表类型，WEEK（周）/MONTH（月）/YEAR（年）
            cursor: 游标，用于分页，默认 0

        Returns:
            饮食时长图表数据
        """
        if not self.client.token and not self.client.login():
            return {}

        params = {
            "catId": cat_id,
            "timezoneId": timezone_id,
            "type": chart_type,
            "cursor": cursor
        }

        resp = self.client._request("token/pet/health/v2/diet/chart/duration", params)

        return resp.get("data") or {}

    def get_timeline(
        self,
        pet_id: str,
        date: str,
        timezone_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> List:
        """
        获取猫咪时间线（活动记录）

        Args:
            pet_id: 猫咪 ID
            date: 日期，格式 "YYYY-MM-DD"
            timezone_id: 时区 ID，如 "Asia/Shanghai"
            device_id: 可选的设备 ID；设备模块调用不要求该参数

        Returns:
            时间线数据列表，包含 EAT（进食）和 DRINK（饮水）等活动记录
        """
        if not self.client.token and not self.client.login():
            return []

        params = {
            "petId": pet_id,
            "date": date,
        }
        if timezone_id:
            params["timezoneId"] = timezone_id
        if device_id:
            params["deviceId"] = device_id

        # 设备模块允许省略 deviceId，而 4.3.9 契约把 deviceId 标为必填。
        # 为保留旧时间线入口，此调用跳过本地必填校验；新 call() 仍强制校验。
        resp = self.client._request(
            "token/pet/health/v3/timeline",
            params,
            enforce_device_id=False,
        )

        return resp.get("data") or []
