#!/usr/bin/env python3
"""CATLINK 4.3.9 设备便捷 API。

本模块提供设备查询和控制的便捷方法，统一复用
:class:`CatLinkBaseClient` 的请求、签名、登录与写保护逻辑。399 条操作的
通用入口见 :class:`catlink_client.operations.CatLinkOperations`。

所有控制方法均需显式 ``allow_write=True`` 或环境变量
``CATLINK_ALLOW_DEVICE_CONTROL=1``。
"""

from typing import Any, Dict, Optional

from .core.utils import camera_auth_pwd, pin_sha256


class CatLinkDeviceAPI:
    """按设备族组织的 4.3.9 便捷调用。"""

    LITTER_MODES = {
        "auto": "00",
        "manual": "01",
        "scheduled": "02",
        "empty": "03",
    }

    def __init__(self, client):
        self.client = client

    # ---------------- 内部 ----------------
    def _dispatch(self, slug: str, *, allow_write=False, **params) -> Dict[str, Any]:
        """经统一派发器发送，自动套用 defaults/derived。"""
        return self.client.operations.call(slug, allow_write=allow_write, **params)

    @staticmethod
    def pin_sha256(pin: str) -> str:
        """4 位 PIN → 线上 signCode/oldSignCode（小写 SHA-256）。"""
        return pin_sha256(pin)

    @staticmethod
    def camera_auth_pwd(plain: str) -> str:
        """绑定类接口明文 authPwd → 大写十六进制 AES 密文。"""
        return camera_auth_pwd(plain)

    # ---------------- 只读查询 ----------------
    def devices(self) -> list:
        """通过 sortedListV2 查询设备；只读，无需 allow_write 授权。

        Returns:
            设备字典列表，兼容直接列表及 devices / devices.records 包装。
        """
        body = self.client.call("token/device/union/sortedListV2", {"type": "NONE"}, "GET")
        return self.client._devices_from_data(body.get("data"))

    def device_info(self, device_id: str) -> Dict[str, Any]:
        body = self.client.call("token/device/info", {"deviceId": device_id}, "GET")
        return (body.get("data") or {}).get("deviceInfo") or {}

    def consumables(self, device_id: str, device_type: str) -> list:
        body = self.client.call(
            "token/device/union/consumableListForOne",
            {"deviceId": device_id, "deviceType": device_type},
            "GET",
        )
        return (body.get("data") or {}).get("listConsumables") or []

    # ---------------- 通用写操作 ----------------
    def rename(self, device_id: str, name: str, *, allow_write=False) -> Dict[str, Any]:
        return self.client.call(
            "token/device/rename",
            {"deviceId": device_id, "deviceName": name},
            "POST",
            allow_write=allow_write,
        )

    # ---------------- 喂食器 ----------------
    def feeder_food_out(
        self, device_id: str, portions: int = 1, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/device/feeder/v2/foodOut",
            {"deviceId": device_id, "foodOutNum": portions},
            "POST",
            allow_write=allow_write,
        )

    def feeder_switch_mode(
        self, device_id: str, run_model: str, *, allow_write=False, **kwargs
    ) -> Dict[str, Any]:
        return self._dispatch(
            "api_token_device_feeder_v2_switchmode",
            allow_write=allow_write,
            deviceId=device_id,
            runModel=run_model,
            **kwargs,
        )

    def feeder_pro_food_out(
        self, device_id: str, portions: int = 1, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/device/feederpro/v2/foodOut",
            {"deviceId": device_id, "foodOutNum": portions},
            "POST",
            allow_write=allow_write,
        )

    def feeder_pro_switch_mode(
        self, device_id: str, run_mode: str, *, allow_write=False, **kwargs
    ) -> Dict[str, Any]:
        return self._dispatch(
            "api_token_device_feederpro_switchmode_v2",
            allow_write=allow_write,
            deviceId=device_id,
            feederproRunMode=run_mode,
            **kwargs,
        )

    def feeder_recalibrate(
        self, device_id: str, pro: bool = False, *, allow_write=False
    ) -> Dict[str, Any]:
        path = (
            "token/device/feederpro/recalibration"
            if pro
            else "token/device/feeder/v2/recalibration"
        )
        return self.client.call(
            path, {"deviceId": device_id}, "POST", allow_write=allow_write
        )

    def feeder_desiccant_reset(
        self, device_id: str, pro: bool = False, *, allow_write=False
    ) -> Dict[str, Any]:
        path = (
            "token/device/feederpro/desiccant/reset"
            if pro
            else "token/device/feeder/v2/desiccant/reset"
        )
        return self.client.call(
            path, {"deviceId": device_id}, "POST", allow_write=allow_write
        )

    def feeder_add_timing(
        self,
        device_id: str,
        hour: str,
        minute: str,
        portions: int,
        weekdays: str = "1,2,3,4,5,6,7",
        pro: bool = True,
        group_id: Optional[str] = None,
        *,
        allow_write=False,
    ) -> Dict[str, Any]:
        setting = f"{hour}:{minute}-{portions}-{weekdays}"
        path = (
            "token/device/feederpro/addTiming/v2"
            if pro
            else "token/device/feeder/v2/addTiming"
        )
        params = {"deviceId": device_id, "timingSetting": setting}
        if group_id is not None:
            params["groupId"] = group_id
        return self.client.call(path, params, "POST", allow_write=allow_write)

    def feeder_timings(self, device_id: str, pro: bool = True) -> list:
        path = (
            "token/device/feederpro/timings"
            if pro
            else "token/device/feeder/v2/timings"
        )
        body = self.client.call(path, {"deviceId": device_id}, "POST")
        return (body.get("data") or {}).get("timings") or []

    def upload_feederpro_sound(
        self,
        device_id: str,
        data: bytes,
        filename: str = "sound.mp3",
        *,
        allow_write=False,
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/feederpro/sound/uploadFile",
            {
                "deviceId": device_id,
                "_files": {"data": data, "filename": filename},
            },
            "POST",
            allow_write=allow_write,
        )

    def feeder_camera_bind(
        self,
        mac: str,
        camera_mac: str,
        auth_name: str,
        auth_pwd: str,
        uid: str,
        *,
        allow_write=False,
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/device/feeder/v2/bind",
            {
                "mac": mac,
                "cameraMac": camera_mac,
                "authName": auth_name,
                "authPwd": camera_auth_pwd(auth_pwd),
                "uid": uid,
            },
            "POST",
            allow_write=allow_write,
        )

    # ---------------- 饮水机 ----------------
    def purepro_run_mode(
        self, device_id: str, mode: str, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/device/purepro/runMode",
            {"deviceId": device_id, "runMode": mode},
            "POST",
            allow_write=allow_write,
        )

    def purepro_filter_reset(
        self, device_id: str, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/device/purepro/filterElement/reset",
            {"deviceId": device_id},
            "POST",
            allow_write=allow_write,
        )

    # ---------------- 猫砂盆 ----------------
    def litter_change_mode(
        self, device_id: str, work_model: str, *, allow_write=False
    ) -> Dict[str, Any]:
        code = self.LITTER_MODES.get(work_model, work_model)
        return self.client.call(
            "token/litterbox/changeMode",
            {"deviceId": device_id, "workModel": code},
            "POST",
            allow_write=allow_write,
        )

    def litter_action_v3(
        self, device_id: str, action: str, behavior: str, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/actionCmd/v3",
            {"deviceId": device_id, "action": action, "behavior": behavior},
            "POST",
            allow_write=allow_write,
        )

    def litter_action(
        self, device_id: str, cmd: str, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/actionCmd",
            {"deviceId": device_id, "cmd": cmd},
            "POST",
            allow_write=allow_write,
        )

    def litter_key_lock(
        self, device_id: str, locked: bool, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/keyLock",
            {"deviceId": device_id, "lockStatus": "01" if locked else "00"},
            "POST",
            allow_write=allow_write,
        )

    def litter_keypad_tone(
        self, device_id: str, on: bool, kind: str = "00", *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/keypadTone",
            {
                "deviceId": device_id,
                "panelTone": "01" if on else "00",
                "kind": kind,
            },
            "POST",
            allow_write=allow_write,
        )

    def litter_quiet_mode(
        self,
        device_id: str,
        enable: bool,
        times: Optional[str] = None,
        *,
        allow_write=False,
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/quietMode",
            {"deviceId": device_id, "enable": enable, "times": times},
            "POST",
            allow_write=allow_write,
        )

    def litter_light(
        self, device_id: str, on: bool, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/indicatorLightSetting",
            {
                "deviceId": device_id,
                "status": "ALWAYS_OPEN" if on else "CLOSED",
            },
            "POST",
            allow_write=allow_write,
        )

    def litter_pave_level(
        self, device_id: str, level: int, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/paveLevel",
            {"deviceId": device_id, "level": level},
            "POST",
            allow_write=allow_write,
        )

    def litter_safe_time(
        self, device_id: str, minutes: int, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/safeTimeSetting",
            {"deviceId": device_id, "safeTime": minutes},
            "POST",
            allow_write=allow_write,
        )

    def litter_litter_type(
        self, device_id: str, code: str, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/catLitterSetting",
            {"deviceId": device_id, "litterType": code},
            "POST",
            allow_write=allow_write,
        )

    def litter_restart(self, device_id: str, *, allow_write=False) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/restart",
            {"deviceId": device_id},
            "POST",
            allow_write=allow_write,
        )

    def litter_auto_burial(
        self, device_id: str, enable: bool, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/deepClean/autoBurial",
            {"deviceId": device_id, "enable": enable},
            "POST",
            allow_write=allow_write,
        )

    def litter_continuous_cleaning(
        self, device_id: str, enable: bool, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/deepClean/continuousCleaning",
            {"deviceId": device_id, "enable": enable},
            "POST",
            allow_write=allow_write,
        )

    def litter_notice(
        self, device_id: str, item: str, enable: bool, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/noticeConfig/set",
            {"deviceId": device_id, "noticeItem": item, "noticeSwitch": enable},
            "POST",
            allow_write=allow_write,
        )

    def litter_add_sand(
        self,
        device_id: str,
        model: Optional[str] = None,
        level: Optional[int] = None,
        *,
        allow_write=False,
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/sanboxSet",
            {"deviceId": device_id, "model": model, "level": level},
            "POST",
            allow_write=allow_write,
        )

    def litter_consumable_reset(
        self,
        device_id: str,
        device_type: str,
        ctype: str,
        *,
        allow_write=False,
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/device/union/consumableReset",
            {
                "deviceId": device_id,
                "deviceType": device_type,
                "consumablesType": ctype,
            },
            "POST",
            allow_write=allow_write,
        )

    def litter_add_timing(
        self,
        device_id: str,
        hour: str,
        minute: str,
        weekdays: str = "1,2,3,4,5,6,7",
        *,
        allow_write=False,
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/addTiming/v2",
            {
                "deviceId": device_id,
                "timingSetting": f"{hour}:{minute}",
                "repeat": weekdays,
            },
            "POST",
            allow_write=allow_write,
        )

    def litter_update_timing(
        self,
        device_id: str,
        timing_id: str,
        hour: str,
        minute: str,
        weekdays: str = "1,2,3,4,5,6,7",
        *,
        allow_write=False,
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/updTiming/v2",
            {
                "deviceId": device_id,
                "timingId": timing_id,
                "timingSetting": f"{hour}:{minute}",
                "repeat": weekdays,
            },
            "POST",
            allow_write=allow_write,
        )

    def litter_toggle_timing(
        self, device_id: str, timing_id: str, enable: bool, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/litterbox/timingToggle/v2",
            {
                "deviceId": device_id,
                "timingId": timing_id,
                "status": 0 if enable else 1,
            },
            "POST",
            allow_write=allow_write,
        )

    def litter_timings(self, device_id: str) -> list:
        body = self.client.call(
            "token/litterbox/timings", {"deviceId": device_id}, "POST"
        )
        return (body.get("data") or {}).get("timings") or []

    # ---------------- 空气净化器 ----------------
    def air_speed(
        self, device_id: str, level: int, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/airpurifier/speedLevel",
            {"deviceId": device_id, "speedLevel": str(level)},
            "POST",
            allow_write=allow_write,
        )

    def air_mode(
        self, device_id: str, mode: str, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/airpurifier/modelSwitch",
            {"deviceId": device_id, "model": mode},
            "POST",
            allow_write=allow_write,
        )

    def air_child_lock(
        self, device_id: str, enable: bool, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/airpurifier/keyLock/setting",
            {"deviceId": device_id, "switchFlag": enable},
            "POST",
            allow_write=allow_write,
        )

    def air_uv(self, device_id: str, enable: bool, *, allow_write=False) -> Dict[str, Any]:
        return self.client.call(
            "token/airpurifier/uvSwitch",
            {"deviceId": device_id, "switchFlag": enable},
            "POST",
            allow_write=allow_write,
        )

    # ---------------- 项圈 ----------------
    def collar_sync_time(self, device_id: str, *, allow_write=False) -> Dict[str, Any]:
        return self.client.call(
            "token/device/collar/cmd/time/sync",
            {"deviceId": device_id},
            "POST",
            allow_write=allow_write,
        )

    def collar_sync_action(
        self, device_id: str, message: str, *, allow_write=False
    ) -> Dict[str, Any]:
        return self.client.call(
            "token/device/collar/cmd/data/syncAction",
            {"deviceId": device_id, "message": message},
            "POST",
            allow_write=allow_write,
        )
