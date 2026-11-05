# CATLINK Client Python

独立、非官方的 CATLINK 云端 API Python 客户端，用于查询智能宠物设备、读取猫咪健康数据及控制设备。

- 提供设备详情、历史记录、宠物时间线、饮食图表和 C07 事件图片查询。
- 设备控制默认关闭，需显式授权；登录过期仅自动重试一次只读请求。

## 安装

下载源码后，在项目目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
cp .env.example .env
```

编辑 `.env`，填写 `CATLINK_PHONE` 和 `CATLINK_PASSWORD`。国内账号默认使用 `CATLINK_REGION=china`；国际区、美国区、新加坡区分别为 `global`、`usa`、`singapore`。其他配置见 [.env.example](.env.example)。

## 快速开始

建议将设备共享给一个专门用于程序调用的小号，并使用该账号登录本客户端。使用主账号登录可能使手机上的 CATLINK App 会话失效，需要重新登录。

```python
import os

from dotenv import load_dotenv
from catlink_client import CatLinkClient

load_dotenv()
client = CatLinkClient(
    phone=os.environ["CATLINK_PHONE"],
    password=os.environ["CATLINK_PASSWORD"],
    region=os.getenv("CATLINK_REGION", "china"),
)
try:
    if not client.login():
        raise RuntimeError("CATLINK 登录失败")

    devices = client.get_devices()
    print(f"找到 {len(devices)} 台设备")
    for device in devices:
        online = device.get("onlineStatus", device.get("online"))
        status = "在线" if online is True else "离线" if online is False else "未知"
        print(
            device.get("deviceName", "未命名设备"),
            device.get("deviceType", "未知类型"),
            f"在线状态：{status}",
            sep=" | ",
        )
finally:
    client.session.close()
```

`client.get_devices()` 优先调用 `GET token/device/union/sortedListV2`；此接口的 `data` 直接返回设备列表。列表为空时，客户端再兼容查询旧接口。`token/device/list` 和 `token/device/union/list/sorted` 可能返回部分设备并漏掉新设备，旧接口返回非空列表也不代表设备齐全。`onlineStatus` 为布尔值，示例显示为在线、离线或未知，并兼容缺少该字段时的 `online`。

也可运行 `python main.py`，按配置查询设备和当天记录。

查询设备详情或直接调用接口：

```python
# 以下片段使用已登录且会话仍打开的 client。
water = client.purepro.get_detail("water_device_id")
feeder = client.feeder_pro.get_detail("feeder_device_id")
info = client.call("token/device/info", {"deviceId": "device_id"}, method="GET")

# 原始设备列表接口：返回完整响应信封，data 为设备列表。
response = client.call("token/device/union/sortedListV2", {"type": "NONE"}, method="GET")
devices = response.get("data") or []
```

查询猫咪当天活动时间线：

```python
from datetime import date

cats = client.cat.get_list("Asia/Shanghai")
if cats:
    timeline = client.cat.get_timeline(
        pet_id=cats[0]["id"],
        date=date.today().isoformat(),
        timezone_id="Asia/Shanghai",
    )
```

需要控制设备时，在具体方法上显式授权：

```python
result = client.feeder_pro.food_out("device_id", portions=1, allow_write=True)

# 也可使用便捷 API 或操作目录。
client.api.litter_restart("device_id", allow_write=True)
client.dispatch("api_token_litterbox_restart", deviceId="device_id", allow_write=True)
```

也可将 `CATLINK_ALLOW_DEVICE_CONTROL=1` 作为整个进程的写授权。未授权写入抛 `DeviceControlBlocked`。`client.call()`、`client.operations.call()` 和 `client.api` 的业务失败抛 `CatlinkAPIError`；协议响应异常抛 `CatLinkProtocolError`。控制请求不会因登录过期自动重发。

## 设备与接口

| 模块 | 设备／能力 |
|---|---|
| `client.feeder` / `client.feeder_pro` | 普通喂食器 / 喂食器 Pro |
| `client.purepro` | 饮水机 |
| `client.scooper` / `client.litter_box_599` | Scooper 猫砂盆 / C1 |
| `client.scooper_pro_ultra` | Scooper Pro Ultra，有限支持 |
| `client.c08` | C08 / Open-X 猫砂盆 |
| `client.visual_c07` | 大白 Pro，实验性只读支持 |
| `client.cat` | 猫咪列表、摘要、时间线与饮食图表 |
| `client.api` | 按设备提供的便捷查询和控制方法 |
| `client.operations` / `client.dispatch()` | 完整操作目录，覆盖空气净化器、项圈、摄像头等 18 个设备族 |

详细方法、参数、返回值和全部操作见 [API 参考](docs/api.md)。其中 5 条操作已禁用并提供替代路径；接口覆盖不代表所有型号都已完成实机验证。C07 尚未完成实机验证。

## 来源与许可证

本项目参考 [hasscc/catlink](https://github.com/hasscc/catlink) 的请求方式和设备协议映射，使用 [Apache License 2.0](LICENSE)。CATLINK 及相关产品名称归各自权利人所有。
