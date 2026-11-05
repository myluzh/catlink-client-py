#!/usr/bin/env python3
"""CATLINK LITTER_BOX_599 (Scooper C1) 猫砂盆设备"""

from typing import Dict, Any

from ..core.base import CatLinkBaseClient


class LitterBoxClient:
    """LITTER_BOX_599 (Scooper C1) 猫砂盆客户端

    这是 Scooper C1 基础版猫砂盆，使用与 SCOOPER 不同的 API 接口
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
        获取猫砂盆设备详情

        Args:
            device_id: 设备 ID

        Returns:
            设备详情
        """
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/info",
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
            "token/litterbox/stats/log/top5",
            {"deviceId": device_id}
        )

        return resp.get("data") or {}

    def change_mode(
        self,
        device_id: str,
        mode: str,
        *, allow_write: bool = False,
    ) -> Dict[str, Any]:
        """
        切换工作模式

        Args:
            device_id: 设备 ID
            mode: 工作模式 (auto/manual/time)

        Returns:
            响应结果
        """
        mode_map = {
            "auto": "00",
            "manual": "01",
            "time": "02",
        }

        work_model = mode_map.get(mode)
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

    def set_action(
        self,
        device_id: str,
        action: str,
        *, allow_write: bool = False,
    ) -> Dict[str, Any]:
        """
        执行动作（清理/暂停）

        Args:
            device_id: 设备 ID
            action: 动作 (Cleaning/Pause)

        Returns:
            响应结果
        """
        action_map = {
            "Cleaning": "01",
            "Pause": "00",
        }

        cmd = action_map.get(action)
        if cmd is None:
            return {"returnCode": -1, "returnMsg": f"Invalid action: {action}"}

        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/actionCmd",
            {
                "deviceId": device_id,
                "cmd": cmd
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def change_garbage_bag(
        self,
        device_id: str,
        enable: bool = True,
        *, allow_write: bool = False,
    ) -> Dict[str, Any]:
        """
        更换垃圾袋

        Args:
            device_id: 设备 ID
            enable: True=更换垃圾袋, False=重置

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/replaceGarbageBagCmd",
            {
                "deviceId": device_id,
                "enable": "1" if enable else "0"
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def set_box_full_sensitivity(
        self,
        device_id: str,
        level: int,
        *, allow_write: bool = False,
    ) -> Dict[str, Any]:
        """
        设置满箱灵敏度等级

        Args:
            device_id: 设备 ID
            level: 灵敏度等级 (1-4)

        Returns:
            响应结果
        """
        if level < 1 or level > 4:
            return {"returnCode": -1, "returnMsg": f"Invalid level: {level}, must be 1-4"}

        level_key = f"LEVEL_{level:02d}"

        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        resp = self.client._request(
            "token/litterbox/boxFullSetting",
            {
                "deviceId": device_id,
                "level": level_key
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def reset_consumable(
        self,
        device_id: str,
        consumables_type: str,
        *, allow_write: bool = False,
    ) -> Dict[str, Any]:
        """
        重置耗材（猫砂或除臭剂）

        Args:
            device_id: 设备 ID
            consumables_type: 耗材类型 (CAT_LITTER/DEODORIZER_02)

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        if not self.client.token and not self.client.login():
            return {}

        # 先获取设备类型
        resp = self.client._request(
            "token/device/union/consumableReset",
            {
                "deviceId": device_id,
                "deviceType": "LITTER_BOX_599",
                "consumablesType": consumables_type
            },
            method="POST",
            allow_write=allow_write,
        )

        return resp

    def reset_litter(self, device_id: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        重置猫砂计数

        Args:
            device_id: 设备 ID

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        return self.reset_consumable(device_id, "CAT_LITTER", allow_write=allow_write)

    def reset_deodorant(self, device_id: str, *, allow_write: bool = False) -> Dict[str, Any]:
        """
        重置除臭剂计数

        Args:
            device_id: 设备 ID

        Returns:
            响应结果
        """
        self.client.require_write(allow_write)
        return self.reset_consumable(device_id, "DEODORIZER_02", allow_write=allow_write)
