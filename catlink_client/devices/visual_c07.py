"""VISUAL_C07（大白 Pro）只读接口。

图片下载不携带 CATLINK 登录凭据。
"""

from typing import Any, Dict, Optional
from urllib.parse import urlsplit

import requests

from ..core.base import CatLinkBaseClient


class VisualC07Client:
    """大白 Pro 的设备状态、补砂状态、时间线和事件图片查询。"""

    MAX_IMAGE_BYTES = 5 * 1024 * 1024

    def __init__(self, base_client: CatLinkBaseClient):
        """初始化客户端。

        Args:
            base_client: 共用登录和签名的基础客户端。
        """
        self.client = base_client

    def get_detail(self, device_id: str) -> Dict[str, Any]:
        """获取 C07 设备详情。

        Args:
            device_id: 设备 ID。

        Returns:
            data.deviceInfo；无数据或登录失败返回空字典。
            原始详情可能含设备标识及授权字段，请勿公开完整响应。
        """
        if not self.client.token and not self.client.login():
            return {}
        resp = self.client._request(
            "token/cameraLitterbox/info", {"deviceId": device_id}
        )
        return (resp.get("data") or {}).get("deviceInfo") or {}

    def get_sand_info(self, device_id: str) -> Dict[str, Any]:
        """获取自动补砂模块状态。

        Args:
            device_id: 设备 ID。

        Returns:
            data.info，包含 workModel、level、install 等原始字段；
            无数据或登录失败返回空字典。
        """
        if not self.client.token and not self.client.login():
            return {}
        resp = self.client._request(
            "token/cameraLitterbox/sandSysInfo", {"deviceId": device_id}
        )
        return (resp.get("data") or {}).get("info") or {}

    def get_logs_timeline(
        self,
        device_id: str,
        date: str,
        page_number: int = 1,
        page_size: int = 20,
        log_type: int = 0,
        sub_type: int = 0,
    ) -> Dict[str, Any]:
        """获取 C07 事件时间线。

        Args:
            device_id: 设备 ID。
            date: 查询日期，格式 YYYY-MM-DD。
            page_number: 页码，默认 1。
            page_size: 每页数量，默认 20。
            log_type: 事件类型，默认 0（全部）。
            sub_type: 事件子类型，默认 0（全部）。

        Returns:
            原始分页数据，事件位于 records；无数据或登录失败返回空字典。
            事件可能包含图片 ID 或签名地址，请勿公开完整响应。
        """
        if not self.client.token and not self.client.login():
            return {}
        return self.client._request(
            "token/litterbox/stats/log/timeline/v2",
            {
                "deviceId": device_id,
                "date": date,
                "pageNumber": page_number,
                "pageSize": page_size,
                "type": log_type,
                "subType": sub_type,
            },
        ).get("data") or {}

    def get_event_image(self, device_id: str, pic_id: str) -> Optional[bytes]:
        """按事件图片 ID 下载 JPEG，不向图片主机发送登录凭据。

        Args:
            device_id: 设备 ID。
            pic_id: 时间线中的 picIdOfPre、picIdOfNext、picIdOfCapture
                或 picIdOfBehind。

        Returns:
            JPEG 字节；登录失败、图片不可用或下载校验失败返回 None。
            只接受阿里云 HTTPS 图片地址，禁止重定向，大小上限 5 MiB。
            获取图片地址的 API 请求异常仍向调用方传播。
        """
        if not pic_id:
            return None
        if not self.client.token and not self.client.login():
            return None
        resp = self.client._request(
            "token/cameraLitterbox/getPicUrl",
            {"deviceId": device_id, "picId": pic_id},
        )
        if resp.get("returnCode") not in (None, 0):
            return None
        url = (resp.get("data") or {}).get("picUrl")
        if not isinstance(url, str):
            return None
        try:
            target = urlsplit(url)
            host = target.hostname or ""
            if (
                target.scheme != "https"
                or not host.endswith(".aliyuncs.com")
                or target.username is not None
                or target.password is not None
                or target.port not in (None, 443)
            ):
                return None
            # 使用独立请求，隔离基础客户端的 token、cookies 和会话认证。
            with requests.get(
                url, stream=True, allow_redirects=False, timeout=10
            ) as response:
                if response.status_code != 200:
                    return None
                content_type = response.headers.get("Content-Type", "")
                if content_type.split(";", 1)[0].strip().lower() != "image/jpeg":
                    return None
                length = response.headers.get("Content-Length")
                if length is not None and not 0 <= int(length) <= self.MAX_IMAGE_BYTES:
                    return None
                chunks = []
                total = 0
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    total += len(chunk)
                    if total > self.MAX_IMAGE_BYTES:
                        return None
                    chunks.append(chunk)
                image = b"".join(chunks)
                return image if image.startswith(b"\xff\xd8\xff") else None
        except (requests.RequestException, ValueError):
            return None
