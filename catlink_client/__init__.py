#!/usr/bin/env python3
"""CATLINK 客户端包。"""

from .core.base import CatLinkBaseClient, is_read_path
from .core.errors import (
    CatLinkError,
    CatLinkHTTPError,
    CatLinkProtocolError,
    CatLinkTransportError,
    CatlinkAPIError,
    CatlinkProtocolError,
    CatlinkTransportError,
    DeviceControlBlocked,
    DisabledOperation,
    MissingParameter,
    UnconfirmedContract,
    UnknownParameter,
)
from .device_api import CatLinkDeviceAPI
from .operations import CatLinkOperations, OPERATIONS
from .read_paths import READ_PATHS
from .devices.feeder import FeederClient
from .devices.feeder_pro import FeederProClient
from .devices.purepro import PureProClient
from .devices.scooper import ScooperClient
from .devices.scooper_pro_ultra import ScooperProUltraClient
from .devices.litter_box_599 import LitterBoxClient
from .devices.c08 import C08Client
from .devices.cat import CatClient
from .devices.visual_c07 import VisualC07Client


__version__ = "26.10.31"


class CatLinkClient(CatLinkBaseClient):
    """CATLINK 客户端主类。

    旧设备模块入口保持不变；4.3.9 全量能力通过 ``client.operations`` 与
    ``client.api`` 使用。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 喂食器
        self.feeder = FeederClient(self)
        self.feeder_pro = FeederProClient(self)
        # 水碗
        self.purepro = PureProClient(self)
        # 猫砂盆
        self.scooper = ScooperClient(self)
        self.scooper_pro_ultra = ScooperProUltraClient(self)
        self.litter_box_599 = LitterBoxClient(self)
        self.c08 = C08Client(self)
        self.visual_c07 = VisualC07Client(self)
        # 猫咪
        self.cat = CatClient(self)


__all__ = [
    "__version__",
    "CatLinkClient",
    "CatLinkBaseClient",
    "CatLinkOperations",
    "CatLinkDeviceAPI",
    "OPERATIONS",
    "READ_PATHS",
    "is_read_path",
    "CatLinkError",
    "CatLinkHTTPError",
    "CatLinkProtocolError",
    "CatLinkTransportError",
    "CatlinkAPIError",
    "CatlinkProtocolError",
    "CatlinkTransportError",
    "DeviceControlBlocked",
    "DisabledOperation",
    "MissingParameter",
    "UnconfirmedContract",
    "UnknownParameter",
    "FeederClient",
    "FeederProClient",
    "PureProClient",
    "ScooperClient",
    "ScooperProUltraClient",
    "LitterBoxClient",
    "C08Client",
    "CatClient",
    "VisualC07Client",
]
