#!/usr/bin/env python3
"""CATLINK 设备模块"""

from .feeder import FeederClient
from .feeder_pro import FeederProClient
from .purepro import PureProClient
from .scooper import ScooperClient
from .scooper_pro_ultra import ScooperProUltraClient
from .litter_box_599 import LitterBoxClient
from .c08 import C08Client
from .cat import CatClient
from .visual_c07 import VisualC07Client

__all__ = [
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
