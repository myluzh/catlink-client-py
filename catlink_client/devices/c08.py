#!/usr/bin/env python3
"""CATLINK C08 猫砂盆设备"""

from typing import Dict, Any, List

from ..core.base import CatLinkBaseClient


class C08Client:
    """C08 猫砂盆客户端"""

    # 模式选项
    MODES = {
        "00": "auto",
        "01": "manual",
        "02": "scheduled",
    }

    # 猫砂类型选项
    LITTER_TYPES = {
        "00": "Bentonite",
        "02": "Mixed",
    }

    # 安全时间选项
    SAFE_TIME_OPTIONS = {
        "1": "1 min",
        "3": "3 min",
        "5": "5 min",
        "7": "7 min",
        "10": "10 min",
        "15": "15 min",
        "30": "30 min",
    }

    # 动作选项
    ACTION_OPTIONS = {
        "Clean: start": ("RUN", "CLEAN"),
        "Clean: pause": ("PAUSE", "CLEAN"),
        "Clean: cancel": ("CANCEL", "CLEAN"),
        "Pave: start": ("RUN", "PAVE"),
        "Pave: pause": ("PAUSE", "PAVE"),
    }

    def __init__(self, base_client: CatLinkBaseClient):
        """
        初始化 C08 客户端

        Args:
            base_client: 基础客户端实例
        """
        self.client = base_client

    # ==================== 数据查询方法 ====================

    def get_detail(self, device_id: str) -> Dict[str, Any]:
        """
        获取 C08 设备详情

        Args:
            device_id: 设备 ID

        Returns:
            设备详情
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/info/c08",
            {"deviceId": device_id}
        )

        return (resp.get("data") or {}).get("deviceInfo") or {}

    def get_logs_top5(self, device_id: str) -> Dict[str, Any]:
        """
        获取 C08 记录 Top5

        Args:
            device_id: 设备 ID

        Returns:
            记录
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/stats/log/top5",
            {"deviceId": device_id}
        )

        data = resp.get("data") or {}
        # C08 的日志在 scooperLogTop5 字段
        return {"scooperLogTop5": data.get("scooperLogTop5") or data.get("logs") or []}

    def get_logs_list(
        self,
        device_id: str,
        date: str,
        page_number: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取 C08 历史记录列表

        Args:
            device_id: 设备 ID
            date: 查询日期，格式 YYYY-MM-DD
            page_number: 页码，默认 1
            page_size: 每页数量，默认 20

        Returns:
            历史记录，包含 total 和 rows
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/stats/log/list",
            {
                "deviceId": device_id,
                "date": date,
                "pageNumber": page_number,
                "pageSize": page_size
            }
        )

        data = resp.get("data") or {}
        return data.get("scooperLogs") or {}

    def get_stats_cats(self, device_id: str) -> Dict[str, Any]:
        """
        获取 C08 猫咪统计数据

        Args:
            device_id: 设备 ID

        Returns:
            统计数据
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/stats/cats",
            {"deviceId": device_id}
        )

        return resp.get("data") or {}

    def get_wifi_info(self, device_id: str) -> Dict[str, Any]:
        """
        获取 WiFi 信息

        Args:
            device_id: 设备 ID

        Returns:
            WiFi 信息 (rssi, wifiName 等)
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/wifi/info",
            {"deviceId": device_id}
        )

        return (resp.get("data") or {}).get("wifiInfo") or {}

    def get_linked_pets(self, device_id: str) -> List:
        """
        获取关联的猫咪列表

        Args:
            device_id: 设备 ID

        Returns:
            关联的猫咪列表
        """
        if not self.client.token and not self.client.login():
            return []

        resp = self.client._request(
            "token/litterbox/linkedPets",
            {"deviceId": device_id}
        )

        return resp.get("data") or []

    def get_selectable_pets(self, device_id: str) -> List:
        """
        获取可选择的猫咪列表

        Args:
            device_id: 设备 ID

        Returns:
            可选择的猫咪列表
        """
        if not self.client.token and not self.client.login():
            return []

        resp = self.client._request(
            "token/litterbox/cat/listSelectable",
            {"deviceId": device_id}
        )

        return (resp.get("data") or {}).get("cats") or []

    def get_notice_config_list(self, device_id: str) -> List:
        """
        获取通知配置列表

        Args:
            device_id: 设备 ID

        Returns:
            通知配置列表
        """
        if not self.client.token and not self.client.login():
            return []

        resp = self.client._request(
            "token/litterbox/noticeConfig/list/c08",
            {"deviceId": device_id}
        )

        return (resp.get("data") or {}).get("noticeConfigs") or []

    def get_device_stats(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备统计数据对比

        Args:
            device_id: 设备 ID

        Returns:
            设备统计数据
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/stats/data/compare/v2",
            {"deviceId": device_id}
        )

        return (resp.get("data") or {}).get("compareData") or {}

    def get_about_device(self, device_id: str) -> Dict[str, Any]:
        """获取 C08 的设备说明信息。

        Args:
            device_id: 设备 ID。

        Returns:
            data.info 字典；无数据或登录失败返回空字典。
        """
        if not self.client.token and not self.client.login():
            return {}
        resp = self.client._request(
            "token/litterbox/aboutDevice", {"deviceId": device_id}
        )
        return (resp.get("data") or {}).get("info") or {}

    # ==================== 控制方法 ====================

    def change_mode(self, device_id: str, mode: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        切换工作模式

        Args:
            device_id: 设备 ID
            mode: 工作模式 (auto/manual/scheduled)

        Returns:
            响应结果
        """
        # 查找模式代码
        work_model = None
        for k, v in self.MODES.items():
            if v == mode:
                work_model = k
                break

        if work_model is None:
            return {"returnCode": -1, "returnMsg": f"Invalid mode: {mode}"}

        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/changeMode",
            {
                "deviceId": device_id,
                "workModel": work_model
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def select_action(self, device_id: str, action: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        执行动作（清理/铺砂）

        Args:
            device_id: 设备 ID
            action: 动作 (Clean: start/Clean: pause/Clean: cancel/Pave: start/Pave: pause)

        Returns:
            响应结果
        """
        action_payload = self.ACTION_OPTIONS.get(action)
        if action_payload is None:
            return {"returnCode": -1, "returnMsg": f"Invalid action: {action}"}

        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/actionCmd/v3",
            {
                "deviceId": device_id,
                "action": action_payload[0],
                "behavior": action_payload[1]
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def select_litter_type(self, device_id: str, litter_type: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        选择猫砂类型

        Args:
            device_id: 设备 ID
            litter_type: 猫砂类型 (Bentonite/Mixed)

        Returns:
            响应结果
        """
        # 查找猫砂类型代码
        type_code = None
        for k, v in self.LITTER_TYPES.items():
            if v == litter_type:
                type_code = k
                break

        if type_code is None:
            return {"returnCode": -1, "returnMsg": f"Invalid litter type: {litter_type}"}

        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/catLitterSetting",
            {
                "deviceId": device_id,
                "litterType": type_code
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def select_safe_time(self, device_id: str, safe_time: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        选择安全时间

        Args:
            device_id: 设备 ID
            safe_time: 安全时间 (1 min/3 min/5 min/7 min/10 min/15 min/30 min)

        Returns:
            响应结果
        """
        # 查找安全时间代码
        safe_value = None
        for k, v in self.SAFE_TIME_OPTIONS.items():
            if v == safe_time:
                safe_value = k
                break

        if safe_value is None:
            return {"returnCode": -1, "returnMsg": f"Invalid safe time: {safe_time}"}

        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/safeTimeSetting",
            {
                "deviceId": device_id,
                "safeTime": safe_value
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_quiet_mode(
        self,
        device_id: str,
        enable: bool,
        start_time: str = "22:00",
        end_time: str = "07:00",
        *, allow_write: bool = False,
    ) -> Dict[str, Any]:
        """
        设置静音模式

        Args:
            device_id: 设备 ID
            enable: 是否启用
            start_time: 开始时间，格式 "HH:MM"，默认 "22:00"
            end_time: 结束时间，格式 "HH:MM"，默认 "07:00"

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        # 4.3.9 真机与参数集：静音时段走 quietMode(enable+times)；
        # deepClean/autoBurial 只接受 deviceId+enable，不承载 times。
        resp = self.client._request(
            "token/litterbox/quietMode",
            {
                "deviceId": device_id,
                "enable": enable,
                "times": f"{start_time}-{end_time}"
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_auto_burial(self, device_id: str, enable: bool, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        设置自动掩埋

        Args:
            device_id: 设备 ID
            enable: 是否启用

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/deepClean/autoBurial",
            {
                "deviceId": device_id,
                "enable": enable
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_continuous_cleaning(self, device_id: str, enable: bool, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        设置持续清洁

        Args:
            device_id: 设备 ID
            enable: 是否启用

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/deepClean/continuousCleaning",
            {
                "deviceId": device_id,
                "enable": enable
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_child_lock(self, device_id: str, enable: bool, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        设置儿童锁

        Args:
            device_id: 设备 ID
            enable: 是否启用

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        # verified-contract + 真机：litterbox/keyLock 使用 01/00，不使用 LOCKED/UNLOCKED。
        status = "01" if enable else "00"

        resp = self.client._request(
            "token/litterbox/keyLock",
            {
                "deviceId": device_id,
                "lockStatus": status
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_indicator_light(self, device_id: str, enable: bool, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        设置指示灯

        Args:
            device_id: 设备 ID
            enable: 是否启用

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        status = "ALWAYS_OPEN" if enable else "CLOSED"

        resp = self.client._request(
            "token/litterbox/indicatorLightSetting",
            {
                "deviceId": device_id,
                "status": status
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_keypad_tone(self, device_id: str, enable: bool, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        设置按键音

        Args:
            device_id: 设备 ID
            enable: 是否启用

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        # 真机：panelTone 与 kind 都是两位数字编码(01/00)，不使用 ENABLED/DISABLED。
        panel_tone = "01" if enable else "00"

        resp = self.client._request(
            "token/litterbox/keypadTone",
            {
                "deviceId": device_id,
                "panelTone": panel_tone,
                "kind": "00"
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_auto_pet_weight_update(self, device_id: str, enable: bool, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        设置自动更新宠物体重

        Args:
            device_id: 设备 ID
            enable: 是否启用

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/pet/weight/autoUpdate",
            {
                "deviceId": device_id,
                "enable": enable
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_kitty_model(self, device_id: str, enable: bool, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        设置幼猫模式

        Args:
            device_id: 设备 ID
            enable: 是否启用

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/kittyModelSwitch",
            {
                "deviceId": device_id,
                "enable": enable
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_notice(
        self,
        device_id: str,
        notice_item: str,
        enable: bool,
        *, allow_write: bool = False,
    ) -> Dict[str, Any]:
        """
        设置通知开关

        Args:
            device_id: 设备 ID
            notice_item: 通知项 (如: LITTERBOX_599_CAT_CAME, REPLACE_GARBAGE Bag等)
            enable: 是否启用

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/noticeConfig/set",
            {
                "deviceId": device_id,
                "noticeItem": notice_item,
                "noticeSwitch": enable
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    # 通知项常量
    NOTICE_ITEMS = {
        "cat_came": ("LITTERBOX_599_CAT_CAME", "Cat came"),
        "box_full": ("LITTERBOX_599_BOX_FULL", "Box full"),
        "replace_garbage_bag": ("REPLACE_GARBAGE_BAG", "Replace garbage bag"),
        "wash_scooper": ("WASH_SCOOPER", "Wash scooper"),
        "replace_deodorant": ("REPLACE_DEODORANT", "Replace deodorant"),
        "litter_not_enough": ("LITTERBOX_599_CAT_LITTER_NOT_ENOUGH", "Litter not enough"),
        "sandbox_not_enough": ("LITTERBOX_599_SANDBOX_NOT_ENOUGHT", "Sandbox not enough"),
        "anti_pinch": ("LITTERBOX_599_ANTI_PINCH", "Anti pinch"),
        "firmware_updated": ("LITTERBOX_599_FIRMWARE_UPDATED", "Firmware updated"),
    }
