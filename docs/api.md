# API 参考

本页说明客户端入口、设备方法与完整操作目录。安装和最小示例见 [README](../README.md)。接口覆盖不代表所有型号均已完成实机验证。

## 入口与返回值

| 入口 | 用途 | 返回值 |
|---|---|---|
| `client.login()` | 登录 | `bool` |
| `client.get_devices()` | 优先查询 V2 设备列表 | 设备列表 |
| `client.get_device_detail(device_id)` | 通用设备详情 | 完整响应信封 |
| `client.feeder` / `client.purepro` 等设备模块 | 常用查询和控制 | 查询通常返回 `data` 或嵌套对象；控制返回完整响应信封 |
| `client.call(path, params, method="POST", allow_write=False)` | 直接调用路径 | 完整响应信封；业务失败抛 `CatlinkAPIError` |
| `client.operations` / `client.dispatch(slug, **params)` | 按操作目录派发 | 同 `client.call()` |
| `client.api` | 按设备提供的便捷方法 | 见方法 docstring |

设备模块查询无数据或初次登录失败时通常返回空字典或空列表。控制调用方需检查 `returnCode == 0`；SCOOPER 等方法遇到无效枚举返回 `returnCode=-1`，不发送请求。`client._request()` 是内部兼容入口，业务失败返回响应信封。

所有控制方法都需要关键字参数 `allow_write=True`，或环境变量 `CATLINK_ALLOW_DEVICE_CONTROL=1`。只读路径用 `client.call()` 不需要写授权；`client.operations.call()` 和 `client.dispatch()` 对目录中的只读 POST 操作也要求写授权。`returnCode == 1002` 仅对只读路径重登并重试一次，控制指令不重发。

## 设备列表

`client.get_devices()` 优先调用 `GET token/device/union/sortedListV2`，参数为 `type=NONE`。V2 响应的 `data` 直接是设备列表；客户端也兼容 `data.devices` 为列表或 `data.devices.records` 为列表的响应结构。

V2 列表为空时，`get_devices()` 再兼容查询 `token/device/list` 和 `token/device/union/list/sorted`。这两个旧接口可能遗漏新设备，返回非空列表也不能作为完整设备清单。`client.api.devices()` 直接查询 V2。

```python
devices = client.get_devices()

# 需要完整响应信封时直接调用 V2，无需写授权。
response = client.call("token/device/union/sortedListV2", {"type": "NONE"}, method="GET")
devices = response.get("data") or []
for device in devices:
    online = device.get("onlineStatus", device.get("online"))
    status = "在线" if online is True else "离线" if online is False else "未知"
    print(device.get("deviceName"), device.get("deviceType"), status)
```

列表中的设备名称、类型和在线状态分别为 `deviceName`、`deviceType`、`onlineStatus`。`onlineStatus` 的 `True` 表示在线，`False` 表示离线；缺少该字段时，示例兼容 `online`，无法判断时显示未知。设备 ID 可用于后续详情、日志和控制方法，无需输出完整响应对象。

## 操作目录用法

```python
# 只检查目录和参数，不发送请求。
families = client.operations.families()
operations = client.operations.search("重启")
operation = client.operations.describe("api_token_litterbox_restart")
path, params = client.operations.build(
    "api_token_litterbox_restart", deviceId="device_id"
)
```

`families()` 返回设备族与操作数，`list_family(name)` 列出某一设备族。`describe()` 中的 `required` 为已核实必填参数，`optional` 为已核实可选参数，`unverified` 为尚未核实必填性的参数。未核实参数可发送，但不会强制补齐或注入默认值。未知字段和缺失的已核实必填字段在本地报错。

目录含 399 条操作，其中 5 条已禁用，并列出替代路径；包内另有 167 条只读路径及 154 条 `deviceId` 必填路径。

## 便捷 API（client.api）

常用方法包括 `devices()`、`device_info(device_id)`、`consumables(device_id)`、`rename()`、喂食器出粮、饮水机模式、猫砂盆控制、空气净化器、项圈和定时任务。还提供 `pin_sha256()`、`camera_auth_pwd()`、`upload_feederpro_sound()` 与 `feeder_camera_bind()`；完整签名见 [device_api.py](../catlink_client/device_api.py)。控制方法同样需要 `allow_write=True`。

定时任务写入格式：猫砂盆为 `HH:mm` 加独立的 `repeat` 星期串；喂食器为 `HH:mm-份数-星期串`。查询返回的定时对象不能直接用作写入载荷。

## FEEDER / FEEDER_PRO

| 方法 | 说明 |
|---|---|
| `client.feeder.get_detail(device_id)` | 设备详情 |
| `client.feeder.get_logs_top5(device_id)` | 最近记录 |
| `client.feeder.food_out(device_id, portions=1)` | 出粮，份数范围参考 1–10 |
| `client.feeder_pro.get_detail(device_id)` | Pro 设备详情 |
| `client.feeder_pro.get_logs_top5(device_id)` | Pro 最近记录 |
| `client.feeder_pro.get_logs_list(device_id, date, page_number=1, page_size=20)` | Pro 历史分页 |
| `client.feeder_pro.get_consumable_list(device_id)` | Pro 耗材信息 |
| `client.feeder_pro.food_out(device_id, portions=1)` | Pro 出粮，1–5 份 |

## PUREPRO

| 方法 | 说明 |
|---|---|
| `client.purepro.get_detail(device_id)` | 设备详情，含出水模式、水量、滤芯状态等原始字段 |
| `client.purepro.get_logs_top5(device_id)` | 最近饮水记录 |
| `client.purepro.get_logs_list(device_id, date, page_number=1, page_size=20)` | 历史分页 |
| `client.purepro.set_run_mode(device_id, mode)` | 设置出水模式 |

模式支持 `CONTINUOUS_SPRING` / `continuous` / `持续涌泉`、`INTERMITTENT_SPRING` / `intermittent` / `间接涌泉`、`INDUCTION_SPRING` / `induction` / `智能涌泉`。常量为 `PureProClient.RUN_MODES`。

## SCOOPER

| 方法 | 说明 |
|---|---|
| `client.scooper.get_detail(device_id)` | 设备详情 |
| `client.scooper.get_logs_top5(device_id)` | 专用接口 `token/device/scooper/stats/log/top5` |
| `client.scooper.change_mode(device_id, mode)` | `auto`、`manual`、`time`、`empty`，或编码 `00`–`03` |
| `client.scooper.set_action(device_id, action)` | `start`、`pause`，或编码 `01`、`00` |

控制示例（会操作真实设备，按需运行）：

```python
result = client.scooper.change_mode("device_id", "auto", allow_write=True)
if result.get("returnCode") == 0:
    result = client.scooper.set_action("device_id", "start", allow_write=True)
```

## LITTER_BOX_599 / Scooper C1

| 方法 | 说明 |
|---|---|
| `client.litter_box_599.get_detail(device_id)` | 设备详情 |
| `client.litter_box_599.get_logs_top5(device_id)` | 最近记录 |
| `client.litter_box_599.change_mode(device_id, mode)` | `auto` / `manual` / `time` |
| `client.litter_box_599.set_action(device_id, action)` | `Cleaning` / `Pause` |
| `client.litter_box_599.change_garbage_bag(device_id, enable=True)` | 更换垃圾袋 |
| `client.litter_box_599.set_box_full_sensitivity(device_id, level)` | 满箱灵敏度 1–4 |
| `client.litter_box_599.reset_consumable(device_id, consumables_type)` | 重置指定耗材 |
| `client.litter_box_599.reset_litter(device_id)` | 重置猫砂计数 |
| `client.litter_box_599.reset_deodorant(device_id)` | 重置除臭剂计数 |

## VISUAL_PRO_ULTRA

| 方法 | 说明 |
|---|---|
| `client.scooper_pro_ultra.get_detail(device_id)` | briefInfo 详情 |
| `client.scooper_pro_ultra.get_logs_top5(device_id)` | 当天最近 5 条事件的分页数据 |
| `client.scooper_pro_ultra.get_logs_timeline(device_id, date, page_number=1, page_size=20, log_type=0, sub_type=0)` | 原始时间线分页数据 |
| `client.scooper_pro_ultra.get_logs_list(device_id, date, page_number=1, page_size=20)` | 提取后的 records 列表 |

## C08 / Open-X

以下方法均位于 `client.c08`；控制方法需 `allow_write=True`。

| 方法 | 说明 |
|---|---|
| `get_detail(device_id)` | 设备详情 |
| `get_logs_top5(device_id)` | 最近记录 |
| `get_logs_list(device_id, date, page_number=1, page_size=20)` | 历史分页 |
| `get_stats_cats(device_id)` | 猫咪统计 |
| `get_wifi_info(device_id)` | WiFi 信息 |
| `get_linked_pets(device_id)` | 已关联猫咪列表 |
| `get_selectable_pets(device_id)` | 可关联猫咪列表 |
| `get_notice_config_list(device_id)` | 通知配置 |
| `get_device_stats(device_id)` | 统计对比 |
| `get_about_device(device_id)` | 设备说明信息，返回 `data.info` |
| `change_mode(device_id, mode)` | `auto` / `manual` / `scheduled` |
| `select_action(device_id, action)` | `Clean: start/pause/cancel`、`Pave: start/pause` |
| `select_litter_type(device_id, litter_type)` | `Bentonite` / `Mixed` |
| `select_safe_time(device_id, safe_time)` | 安全等待时间，参考 `C08Client.SAFE_TIME_OPTIONS` |
| `set_quiet_mode(device_id, enable, start_time, end_time)` | 静音时段 |
| `set_auto_burial(device_id, enable)` | 自动掩埋 |
| `set_continuous_cleaning(device_id, enable)` | 持续清洁 |
| `set_child_lock(device_id, enable)` | 儿童锁 |
| `set_indicator_light(device_id, enable)` | 指示灯 |
| `set_keypad_tone(device_id, enable)` | 按键音 |
| `set_auto_pet_weight_update(device_id, enable)` | 自动更新宠物体重 |
| `set_kitty_model(device_id, enable)` | 幼猫模式 |
| `set_notice(device_id, notice_item, enable)` | 通知开关 |

可用选项还可查询 `C08Client.MODES`、`LITTER_TYPES`、`ACTION_OPTIONS`、`NOTICE_ITEMS`。

## VISUAL_C07 / 大白 Pro

| 方法 | 说明 |
|---|---|
| `client.visual_c07.get_detail(device_id)` | C07 详情，返回 `data.deviceInfo` |
| `client.visual_c07.get_sand_info(device_id)` | 补砂模块状态，返回 `data.info` |
| `client.visual_c07.get_logs_timeline(device_id, date, page_number=1, page_size=20, log_type=0, sub_type=0)` | 原始时间线分页数据，事件位于 `records` |
| `client.visual_c07.get_event_image(device_id, pic_id)` | JPEG 字节；图片不可用或校验失败返回 `None` |

```python
from pathlib import Path

info = client.visual_c07.get_detail("device_id")
sand = client.visual_c07.get_sand_info("device_id")
page = client.visual_c07.get_logs_timeline("device_id", "2026-10-30")

for event in page.get("records") or []:
    pic_id = next((event.get(key) for key in (
        "picIdOfPre", "picIdOfNext", "picIdOfCapture", "picIdOfBehind"
    ) if event.get(key)), None)
    if pic_id:
        image = client.visual_c07.get_event_image("device_id", pic_id)
        if image:
            Path("event.jpg").write_bytes(image)
        break
```

图片下载只接受阿里云 HTTPS 地址，不携带 CATLINK 会话凭据，不跟随重定向，校验 JPEG 类型及文件头，最大 5 MiB。C07 详情和事件会保留 API 原始字段，可能含授权信息或签名地址，示例仅处理需要的字段。

## 猫咪健康数据

| 方法 | 说明 |
|---|---|
| `client.cat.get_list(timezone_id=None)` | 猫咪列表 |
| `client.cat.get_summary(pet_id, date, timezone_id=None, sport=1)` | 健康摘要 |
| `client.cat.get_timeline(pet_id, date, timezone_id=None, device_id=None)` | 当日活动时间线；旧调用可不传 `device_id` |
| `client.cat.get_diet_chart_intake(cat_id, timezone_id, chart_type="WEEK", cursor=0)` | 饮食摄入图表 |
| `client.cat.get_diet_chart_duration(cat_id, timezone_id, chart_type="WEEK", cursor=0)` | 饮食时长图表 |

图表类型为 `WEEK` / `MONTH` / `YEAR`。日期格式为 `YYYY-MM-DD`，国内查询建议显式使用 `Asia/Shanghai`。

## 记录字段差异

不同设备的日志格式不同，不能按同一种结构解析：

| 数据 | 喂食器日志 | PUREPRO 日志 |
|---|---|---|
| 时长 | `firstSection`，如 `86s` | 通常在 `event` 文本中，如“饮水, 67秒” |
| 摄入量 | `secondSection`，如 `6g` | 不保证提供饮水量 |
| 分页记录 | 按对应接口的实际返回结构取值 | `data.pureLogs.rows` |

猫咪健康时间线的事件类型字段为 `eventType`，设备日志通常为 `type`；使用时以实际响应为准。

## 错误处理

异常均可从 `catlink_client` 导入。

| 异常 | 含义 |
|---|---|
| `CatLinkError` | 客户端错误基类 |
| `CatLinkTransportError` | 网络或超时失败 |
| `CatLinkHTTPError` | HTTP 3xx / 4xx / 5xx |
| `CatLinkProtocolError` | 非对象 JSON、缺失或非法 `returnCode` 等协议异常 |
| `CatlinkAPIError` | `client.call()`、派发器、便捷 API 返回业务错误；可读 `return_code` |
| `DeviceControlBlocked` | 写操作未授权 |
| `MissingParameter` / `UnknownParameter` | 缺少必填参数或传入未知参数 |
| `DisabledOperation` / `UnconfirmedContract` | 已禁用操作或契约未确认 |

异常文本不包含会话凭据；原始响应可能含设备标识或授权字段，请按需提取。`client.cat.get_timeline()` 可不传 `device_id`；直接通过 `client.call()` 调用同一路径时仍强制该参数。未传设备 ID 的时间线调用是否被服务端接受尚未验证。

## 完整操作目录

取值中的“推断”表示尚未验证；协议取值不保证适用于每个设备型号。路径含 `api/` 前缀，`client.call()` 同样接受省略此前缀的路径。

<!-- operations:start -->

### 通用(所有设备)（18）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 绑定设备 | `api/token/device/bind` | — | — | mac | 仅需 `deviceId` |
| 校准 | `api/token/device/calibration` | — | — | deviceId, action, weight | 动作编码(推断) |
| 猫砂类型 | `api/token/device/catLitterSetting` | — | — | deviceId, litterType | `00`=膨润土 / `02`=混合 |
| defaultToggle | `api/token/device/defaultToggle` | — | — | deviceId, defaultStatus | `true` / `false`(推断) |
| defaultVoice | `api/token/device/defaultVoice` | — | — | deviceId, defaultVoice | 设备 ID(推断) |
| 固件升级 | `api/token/device/firmware/update` | deviceId, version | — | — | 固件版本号 |
| 解绑设备 | `api/token/device/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 耗材复位 | `api/token/device/union/consumableReset` | — | — | deviceType, deviceId, consumablesType | `consumablesType`=`CAT_LITTER` / `DEODORIZER_02` |
| 恢复出厂 | `api/token/device/union/maintanence/reset` | — | — | deviceId, type, deviceModel, maintenanceType | `maintenanceType` 指定耗材类别 |
| 除臭设置 | `api/token/device/deodorization/set` | — | — | deviceId, gear | (推断) |
| consumablePeriodReset | `api/token/device/union/consumablePeriodReset` | — | — | deviceType, deviceId, consumablesType, period | 耗材类型(推断) |
| netDistributeHelp | `api/token/device/union/netDistributeHelp` | type, mac, contact, accept | — | — | (推断) |
| netDistributeLog | `api/token/device/union/netDistributeLog` | remark, osType | type, mac | — | — |
| set | `api/token/device/union/validityDays/set` | — | — | deviceId, type, deviceModel, maintenanceType, days | (推断) |
| virtualData | `api/token/device/union/virtualData` | — | — | deviceType | (推断) |
| V2 | `api/token/device/union/virtualData/V2` | — | — | deviceType | (推断) |
| virtualDataForVideo | `api/token/device/union/virtualDataForVideo` | deviceType | — | — | (推断) |
| V2 | `api/token/device/union/virtualDataForVideo/V2` | deviceType | — | — | (推断) |

### SCOOPER 猫砂盆 599/C1（64）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 启动/暂停 | `api/token/litterbox/actionCmd` | — | — | deviceId, cmd | `cmd`=`01`(开始清理)/`00`(暂停) |
| 启动/暂停 v2 | `api/token/litterbox/actionCmd/v2` | deviceId, behavior, action | copies | — | 同 actionCmd |
| 新增定时任务 | `api/token/litterbox/addTiming` | — | — | deviceId, timingSetting | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 新增定时任务 | `api/token/litterbox/addTiming/v2` | — | — | deviceId, timingSetting, repeat | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 自动清理/定时清理 | `api/token/litterbox/autoClean` | deviceId, switchFlag | — | — | 仅需 `deviceId` |
| 绑定设备 | `api/token/litterbox/bind` | — | — | mac | 仅需 `deviceId` |
| 绑定设备 | `api/token/litterbox/bind/v2` | — | — | mac | 仅需 `deviceId` |
| 集便仓满/灵敏度 | `api/token/litterbox/boxFullSetting` | — | — | deviceId, level | 档位 1–4 |
| 集便仓满/灵敏度 | `api/token/litterbox/boxfullSensitivity` | — | — | deviceId, level | `level`=整数档位;MODEL_00 存在不支持的情况，可能返回 returnCode=1 |
| 校准 | `api/token/litterbox/calibration` | deviceId, action, weight | — | — | 仅需 `deviceId` |
| 绑定设备 | `api/token/litterbox/cat/bind` | — | — | deviceId, petId | 猫咪/宠物 ID(推断) |
| 解绑设备 | `api/token/litterbox/cat/unbind` | deviceId, petId | — | — | 仅需 `deviceId` |
| 猫砂类型 | `api/token/litterbox/catLitterSetting` | deviceId, litterType | — | — | `00`=膨润土 / `02`=混合 |
| 切换工作模式 | `api/token/litterbox/changeMode` | deviceId, workModel | — | — | `00`=感应 / `01`=手动 / `02`=定时 |
| 5分钟后掩埋 | `api/token/litterbox/deepClean/fiveMinBurial` | — | — | deviceId, enable | `true` / `false`(推断) |
| 删除定时任务 | `api/token/litterbox/delTiming` | — | — | deviceId, timingId | 设备 ID(推断) |
| 删除定时任务 | `api/token/litterbox/delTiming/v2` | — | — | deviceId, timingId | 设备 ID(推断) |
| 恢复出厂 | `api/token/litterbox/deodorant/reset` | — | — | deviceId | 设备 ID(推断) |
| 除臭设置 | `api/token/litterbox/deodorantSetting` | — | — | deviceId, enable | `true` / `false`(推断) |
| 固件升级 | `api/token/litterbox/firmware/update` | deviceId, version | — | — | 固件版本号 |
| 新风模式 | `api/token/litterbox/freshSysModelSet` | — | — | deviceId, model, level | 整数档位 |
| 新风定时 | `api/token/litterbox/freshSysTimerEdit` | — | — | deviceId, startTimer, endTimer, timerEnable | 设备 ID(推断) |
| 灯光设置 | `api/token/litterbox/indicatorLightSetting` | — | — | deviceId, status | `CLOSED` / `ALWAYS_OPEN` |
| 红外校准 | `api/token/litterbox/infraredCalibrate` | — | — | deviceId | 设备 ID(推断) |
| 童锁开关 | `api/token/litterbox/keyLock` | deviceId, lockStatus | — | — | `lockStatus`=`"00"/"01"` |
| 恢复出厂 | `api/token/litterbox/litter/garbageBag/reset` | — | — | deviceId, times, flag | `HH:mm-HH:mm` |
| 恢复出厂 | `api/token/litterbox/litter/time/reset` | deviceId | — | — | 仅需 `deviceId` |
| 通知开关 | `api/token/litterbox/noticeConfig/set` | — | — | deviceId, noticeItem, noticeSwitch | 通知项枚举 |
| 按键音开关 | `api/token/litterbox/paneltone` | — | — | deviceId, enable | `00`/`01` |
| 铺砂档位 | `api/token/litterbox/paveLevel` | — | — | deviceId, level | `level`=整数档位;部分设备可能不支持（详情 sandPaveLevel 为 null） |
| 宠物体重自动更新 | `api/token/litterbox/pet/weight/autoUpdate` | — | — | deviceId, enable | `true` / `false`(推断) |
| 免打扰/静音时段 | `api/token/litterbox/quietMode` | — | — | deviceId, enable, times | `true` / `false`(推断) |
| 重命名 | `api/token/litterbox/rename` | — | — | deviceId, deviceName | 仅需 `deviceId` |
| 恢复出厂 | `api/token/litterbox/reset` | deviceId | — | — | 仅需 `deviceId` |
| 重置加砂仓状态 | `api/token/litterbox/resetAddSandBoxStatus` | — | — | deviceId | 设备 ID(推断) |
| 重启设备 | `api/token/litterbox/restart` | deviceId | — | — | 仅需 `deviceId` |
| 安全等待时间 | `api/token/litterbox/safeTimeSetting` | deviceId, safeTime | — | — | 分钟串 `1/3/5/7/10/15/30` |
| 加砂设置 | `api/token/litterbox/sanboxSet` | — | — | deviceId, model, level, copies | 整数档位 |
| setVoice | `api/token/litterbox/setVoice` | — | — | deviceId, lockStatus | `00`=解锁 / `01`=上锁 |
| 如厕数据切片 | `api/token/litterbox/sliceToiletData` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 软便等待时间 | `api/token/litterbox/softStoolTimeSetting` | — | — | deviceId, timePeriod | 设备 ID(推断) |
| 恢复出厂 | `api/token/litterbox/stat/reset` | deviceId | — | — | 仅需 `deviceId` |
| 自动清理/定时清理 | `api/token/litterbox/timerClean` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 定时任务开关 | `api/token/litterbox/timingToggle` | — | — | deviceId, timingId, status | 枚举字符串 |
| 定时任务开关 | `api/token/litterbox/timingToggle/v2` | — | — | deviceId, timingId, status | 枚举字符串 |
| 定时任务列表 | `api/token/litterbox/timings` | — | — | deviceId | 设备 ID(推断) |
| 解绑设备 | `api/token/litterbox/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 修改定时任务 | `api/token/litterbox/updTiming` | — | — | deviceId, timingSetting, timingId | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 修改定时任务 | `api/token/litterbox/updTiming/v2` | — | — | deviceId, timingId, timingSetting, repeat | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 多猫识别 | `api/token/litterbox/value/multiCatPayment/link` | — | — | deviceId, timezoneId, deviceType | 设备 ID(推断) |
| 多猫识别 | `api/token/litterbox/value/multiCatPayment/result` | orderNo | — | — | 仅需 `deviceId` |
| allTimingToggle | `api/token/litterbox/allTimingToggle` | — | — | deviceId, enable | `true` / `false`(推断) |
| deviceVipTransfer | `api/token/litterbox/extend/deviceVipTransfer` | — | — | currentDeviceId, targetMac | (推断) |
| getDeodorantLink | `api/token/litterbox/getDeodorantLink` | deviceId | — | — | 仅需 `deviceId` |
| getMultiCatRegLink | `api/token/litterbox/getMultiCatRegLink` | — | — | deviceId | 仅需 `deviceId` |
| preOpenMultiCatReg | `api/token/litterbox/preOpenMultiCatReg` | — | — | deviceId | 仅需 `deviceId` |
| queryCalibration | `api/token/litterbox/queryCalibration` | — | — | deviceId | 仅需 `deviceId` |
| queryInfraredResult | `api/token/litterbox/queryInfraredResult` | — | — | deviceId | 仅需 `deviceId` |
| queryLitterType | `api/token/litterbox/queryLitterType` | deviceId | — | — | 仅需 `deviceId` |
| queryRegResult | `api/token/litterbox/queryRegResult` | — | — | deviceId | 仅需 `deviceId` |
| 取消分享 | `api/token/litterbox/shareDelete` | — | — | deviceId, sharerId | (推断) |
| set | `api/token/litterbox/silentUpgrade/set` | deviceId, silentUpgrade | — | — | — |
| modifyData | `api/token/litterbox/stats/log/modifyData` | — | — | deviceId, eventId, petId, snType, type | 宠物 ID(推断) |
| remove | `api/token/litterbox/stats/log/remove` | — | — | deviceId, logTypeAndIds | (推断) |

### C08 / C08 Pro / SE2（39）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| v2 | `api/token/cameraLitterbox/actionCmd/v2` | deviceId, behavior, action | copies | — | 动作编码(推断) |
| 新增定时任务 | `api/token/cameraLitterbox/addTiming/v2` | — | — | deviceId, timingSetting, repeat | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 自动清理/定时清理 | `api/token/cameraLitterbox/autoClean` | deviceId, switchFlag | — | — | 仅需 `deviceId` |
| 绑定设备 | `api/token/cameraLitterbox/bind` | — | — | mac, deviceSerial, validateCode, deviceModel, deviceType, timezoneId | 待定 |
| 集便仓满/灵敏度 | `api/token/cameraLitterbox/boxfullSensitivity` | — | — | deviceId, level | `level` 整数 |
| 校准 | `api/token/cameraLitterbox/calibration` | — | — | deviceId, action, weight | 动作编码(推断) |
| 摄像头开关 | `api/token/cameraLitterbox/cameraSwitch` | — | — | deviceId, cameraSwitch | 设备 ID(推断) |
| 绑定设备 | `api/token/cameraLitterbox/cat/bind` | deviceId, petId | collarsCode | — | 猫咪/宠物 ID(推断) |
| 解绑设备 | `api/token/cameraLitterbox/cat/unbind` | — | — | deviceId, petId | 猫咪/宠物 ID(推断) |
| 猫砂类型 | `api/token/cameraLitterbox/catLitterSetting` | deviceId, litterType | — | — | `00`=膨润土 / `02`=混合 |
| 删除定时任务 | `api/token/cameraLitterbox/delTiming/v2` | — | — | deviceId, timingId | 设备 ID(推断) |
| 灯光设置 | `api/token/cameraLitterbox/fillLightSetting` | — | — | deviceId, status | 枚举字符串 |
| 固件升级 | `api/token/cameraLitterbox/firmware/updateStatus` | — | — | deviceId, module | 设备 ID(推断) |
| 固件升级 | `api/token/cameraLitterbox/firmware/updateStatusFromYs` | — | — | deviceId | 设备 ID(推断) |
| 新风模式 | `api/token/cameraLitterbox/freshSysModelSet` | — | — | deviceId, model, level | 整数档位 |
| 新风定时 | `api/token/cameraLitterbox/freshSysTimerEdit` | — | — | deviceId, startTimer, endTimer, timerEnable | 设备 ID(推断) |
| 童锁开关 | `api/token/cameraLitterbox/keyLock` | — | — | deviceId, lockStatus | `lockStatus`=`true/false` |
| 幼猫模式 | `api/token/cameraLitterbox/kittyModelSwitch` | deviceId, enable | — | — | `enable`(接口签名 `@c("enable") boolean`) |
| 通知开关 | `api/token/cameraLitterbox/noticeConfig/set` | — | — | deviceId, noticeItem, noticeSwitch | 通知项枚举 |
| 按键音开关 | `api/token/cameraLitterbox/paneltone` | — | — | deviceId, enable | `true` / `false`(推断) |
| 铺砂档位 | `api/token/cameraLitterbox/paveLevel` | — | — | deviceId, level | `level` 整数 |
| 免打扰/静音时段 | `api/token/cameraLitterbox/quietMode` | — | — | deviceId, enable, times | `true` / `false`(推断) |
| 恢复出厂 | `api/token/cameraLitterbox/reset` | deviceId | — | — | 仅需 `deviceId` |
| 重置加砂仓状态 | `api/token/cameraLitterbox/resetAddSandBoxStatus` | — | — | deviceId | 设备 ID(推断) |
| 重启设备 | `api/token/cameraLitterbox/restart` | deviceId | — | — | 仅需 `deviceId` |
| 安全等待时间 | `api/token/cameraLitterbox/safeTimeSetting` | deviceId, safeTime | — | — | 仅需 `deviceId` |
| 加砂设置 | `api/token/cameraLitterbox/sanboxSet` | — | — | deviceId, model, level, copies | 整数档位 |
| 自动清理/定时清理 | `api/token/cameraLitterbox/timerClean` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 定时任务开关 | `api/token/cameraLitterbox/timingToggle/v2` | — | — | deviceId, timingId, status | 枚举字符串 |
| 定时任务列表 | `api/token/cameraLitterbox/timings` | — | — | deviceId | 设备 ID(推断) |
| 解绑设备 | `api/token/cameraLitterbox/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 修改定时任务 | `api/token/cameraLitterbox/updTiming/v2` | — | — | deviceId, timingId, timingSetting, repeat | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 语音提示 | `api/token/cameraLitterbox/voicePromptSwitch` | — | — | deviceId, enable | `true` / `false`(推断) |
| 水印开关 | `api/token/cameraLitterbox/watermarkSwitch` | deviceId, enable | — | — | `true` / `false`(推断) |
| checkPetFaceReg | `api/token/cameraLitterbox/checkPetFaceReg` | — | — | deviceId, appVersion | (推断) |
| continuousCleaning | `api/token/cameraLitterbox/continuousCleaning` | — | — | deviceId, enable | `true` / `false`(推断) |
| 固件 | `api/token/cameraLitterbox/firmware/doUpdate` | — | — | deviceId | 仅需 `deviceId` |
| queryCalibration | `api/token/cameraLitterbox/queryCalibration` | — | — | deviceId | 仅需 `deviceId` |
| queryLitterType | `api/token/cameraLitterbox/queryLitterType` | deviceId | — | — | 仅需 `deviceId` |

### C07 大白 Pro（24）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 新增定时任务 | `api/token/visualScooper/addTiming` | deviceId, timingSetting | groupId | — | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 校准 | `api/token/visualScooper/calibration` | — | — | deviceId, action, weight | 仅需 `deviceId` |
| 绑定设备 | `api/token/visualScooper/cat/bind` | deviceId, petId | collarsCode | — | 仅需 `deviceId` |
| 解绑设备 | `api/token/visualScooper/cat/unbind` | deviceId, petId | — | — | 猫咪/宠物 ID(推断) |
| 安全锁 PIN | `api/token/visualScooper/closeSec` | deviceId, signCode | — | — | signCode/oldSignCode 为 4 位 PIN 的 SHA-256 小写十六进制(RSAUtils.sha256,勿传明文 PIN) |
| 批量关闭/删除定时 | `api/token/visualScooper/closeTimingList` | — | — | deviceId, timingIds | 设备 ID(推断) |
| 删除定时任务 | `api/token/visualScooper/delTiming` | — | — | deviceId, timingId | 设备 ID(推断) |
| 恢复出厂 | `api/token/visualScooper/deodorant/reset` | deviceId | — | — | 仅需 `deviceId` |
| 恢复出厂 | `api/token/visualScooper/litter/reset` | deviceId | — | — | 仅需 `deviceId` |
| 安全锁 PIN | `api/token/visualScooper/modifySec` | deviceId, signCode, oldSignCode | — | — | signCode/oldSignCode 为 4 位 PIN 的 SHA-256 小写十六进制(RSAUtils.sha256,勿传明文 PIN) |
| 宠物体重自动更新 | `api/token/visualScooper/pet/weight/autoUpdate` | — | — | deviceId, enable | `true` / `false`(推断) |
| 免打扰/静音时段 | `api/token/visualScooper/quietMode` | deviceId, enable | times | — | `HH:mm-HH:mm` |
| 解除保护 | `api/token/visualScooper/releaseProtection` | — | — | deviceId, bizType | 设备 ID(推断) |
| 重命名 | `api/token/visualScooper/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/visualScooper/reset` | deviceId | — | — | 仅需 `deviceId` |
| 安全锁 PIN | `api/token/visualScooper/setSec` | deviceId, signCode | — | — | signCode/oldSignCode 为 4 位 PIN 的 SHA-256 小写十六进制(RSAUtils.sha256,勿传明文 PIN) |
| 序列号开关 | `api/token/visualScooper/snSwitch` | — | — | deviceId, snEnable | `true` / `false`(推断) |
| 定时任务开关 | `api/token/visualScooper/timingToggle` | — | — | deviceId, timingId, status | 枚举字符串 |
| 定时任务列表 | `api/token/visualScooper/timings` | — | — | deviceId | 设备 ID(推断) |
| 解绑设备 | `api/token/visualScooper/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 修改定时任务 | `api/token/visualScooper/updTiming` | — | — | deviceId, timingSetting, timingId | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 安全锁 PIN | `api/token/visualScooper/verifySec` | deviceId, signCode | — | — | signCode/oldSignCode 为 4 位 PIN 的 SHA-256 小写十六进制(RSAUtils.sha256,勿传明文 PIN) |
| allTimingToggle | `api/token/visualScooper/allTimingToggle` | — | — | deviceId, enable | `true` / `false`(推断) |
| operationLog | `api/token/visualScooper/operationLog` | — | — | operationType, deviceId | (推断) |

### 分离式猫砂盆（38）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 新增定时任务 | `api/token/detachableLitterbox/addTiming/v2` | — | — | deviceId, timingSetting, repeat | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 绑定设备 | `api/token/detachableLitterbox/bind` | — | — | mac, deviceSerial, validateCode, deviceModel, deviceType, timezoneId | 待定 |
| 校准 | `api/token/detachableLitterbox/calibration` | — | — | deviceId, action, weight | 动作编码(推断) |
| 绑定设备 | `api/token/detachableLitterbox/cat/bind` | — | — | deviceId, petId | 猫咪/宠物 ID(推断) |
| 解绑设备 | `api/token/detachableLitterbox/cat/unbind` | — | — | deviceId, petId | 猫咪/宠物 ID(推断) |
| 猫砂类型 | `api/token/detachableLitterbox/catLitterSetting` | deviceId, litterType | — | — | `00`=膨润土 / `02`=混合 |
| 切换工作模式 | `api/token/detachableLitterbox/changeMode` | — | — | deviceId, workModel | 同 changeMode,`00/01/02` |
| 光幕检测 | `api/token/detachableLitterbox/curtainDetectionSwitch` | — | — | deviceId, enable | `true` / `false`(推断) |
| 软便处理模式 | `api/token/detachableLitterbox/deepClean/softModel` | — | — | deviceId, enable | `true` / `false`(推断) |
| 删除定时任务 | `api/token/detachableLitterbox/delTiming/v2` | — | — | deviceId, timingId | 设备 ID(推断) |
| 红外开关 | `api/token/detachableLitterbox/infraredSwitch` | — | — | deviceId, enable | `true` / `false`(推断) |
| 光幕配置 | `api/token/detachableLitterbox/lightCurtainInfraredConfig` | — | — | — | 仅需 `deviceId` |
| 通知开关 | `api/token/detachableLitterbox/noticeConfig/set` | — | — | deviceId, noticeItem, noticeSwitch | 通知项枚举 |
| 免打扰/静音时段 | `api/token/detachableLitterbox/quietMode` | — | — | deviceId, enable, times | `true` / `false`(推断) |
| 恢复出厂 | `api/token/detachableLitterbox/reset` | deviceId | — | — | 仅需 `deviceId` |
| 重启设备 | `api/token/detachableLitterbox/restart` | deviceId | — | — | 仅需 `deviceId` |
| 软便等待时间 | `api/token/detachableLitterbox/softStoolTimeSetting` | — | — | deviceId, timePeriod | 设备 ID(推断) |
| 定时任务开关 | `api/token/detachableLitterbox/timingToggle/v2` | — | — | deviceId, timingId, status | 枚举字符串 |
| 定时任务列表 | `api/token/detachableLitterbox/timings` | — | — | deviceId | 设备 ID(推断) |
| 解绑设备 | `api/token/detachableLitterbox/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 修改定时任务 | `api/token/detachableLitterbox/updTiming/v2` | — | — | deviceId, timingId, timingSetting, repeat | **写入** `timingSetting`=`HH:mm` + `repeat`=星期串;查询返回的 JSON 对象不可直接作为写入载荷 |
| 清理/铺砂/启停 | `api/token/detachableLitterbox/actionCmd/v2` | — | — | deviceId, behavior, action, copies | — |
| 摄像头开关 | `api/token/detachableLitterbox/cameraSwitch` | — | — | deviceId, cameraSwitch | — |
| continuousCleaning | `api/token/detachableLitterbox/continuousCleaning` | — | — | deviceId, enable | — |
| faceRecordStart | `api/token/detachableLitterbox/faceRecordStart` | — | — | deviceId, petId | 宠物 ID(推断) |
| 童锁开关 | `api/token/detachableLitterbox/keyLock` | — | — | deviceId, lockStatus | `lockStatus`=`true/false` |
| 幼猫模式 | `api/token/detachableLitterbox/kittyModelSwitch` | — | — | deviceId, enable | — |
| 灯光设置 | `api/token/detachableLitterbox/panelIndicatorLight` | — | — | deviceId, status | — |
| 按键音开关 | `api/token/detachableLitterbox/paneltone` | — | — | deviceId, enable | — |
| 体重自动更新 | `api/token/detachableLitterbox/pet/weight/autoUpdate` | — | — | deviceId, enable | — |
| 分享 | `api/token/detachableLitterbox/preShare` | — | — | deviceId, targetMobileCode, targetMobile, targetEmail | — |
| queryCalibration | `api/token/detachableLitterbox/queryCalibration` | — | — | deviceId | 仅需 `deviceId` |
| queryLitterType | `api/token/detachableLitterbox/queryLitterType` | deviceId | — | — | 仅需 `deviceId` |
| 安全等待时间 | `api/token/detachableLitterbox/safeTimeSetting` | — | — | deviceId, safeTime | — |
| 分享 | `api/token/detachableLitterbox/share` | — | — | deviceId, targetMobile, targetEmail | — |
| 取消分享 | `api/token/detachableLitterbox/shareDelete` | — | — | deviceId, sharerId | — |
| 共享成员 | `api/token/detachableLitterbox/sharers` | — | — | deviceId | — |
| 水印开关 | `api/token/detachableLitterbox/watermarkSwitch` | — | — | deviceId, enable | — |

### FEEDER 普通喂食器（33）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 绑定设备 | `api/token/device/feeder/bind` | — | — | mac | 仅需 `deviceId` |
| defaultToggle | `api/token/device/feeder/defaultToggle` | — | — | deviceId, defaultStatus | `true` / `false`(推断) |
| defaultVoice | `api/token/device/feeder/defaultVoice` | — | — | deviceId, defaultVoice | 设备 ID(推断) |
| 固件升级 | `api/token/device/feeder/firmware/update` | deviceId, version | — | — | 仅需 `deviceId` |
| 出粮(手动喂食) | `api/token/device/feeder/foodOut` | — | — | deviceId, footOutNum | `footOutNum` 份数(注意拼写 footOutNum) |
| 解绑设备 | `api/token/device/feeder/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 新增定时任务 | `api/token/device/feeder/v2/addTiming` | deviceId, timingSetting | groupId | — | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);查询返回的 JSON 对象不可直接作为写入载荷 |
| 绑定设备 | `api/token/device/feeder/v2/bind` | mac | cameraMac, authName, authPwd, uid | — | 待定 |
| 绑定设备 | `api/token/device/feeder/v2/cat/bind` | deviceId, petId | collarsCode | — | 猫咪/宠物 ID(推断) |
| 解绑设备 | `api/token/device/feeder/v2/cat/unbind` | deviceId, petId | — | — | 猫咪/宠物 ID(推断) |
| 安全锁 PIN | `api/token/device/feeder/v2/closeSec` | deviceId, signCode | — | — | signCode/oldSignCode 为 4 位 PIN 的 SHA-256 小写十六进制(RSAUtils.sha256,勿传明文 PIN) |
| 批量关闭/删除定时 ❌服务端404 → 用 `api/token/device/feederpro/closeTimingList` | `api/token/device/feeder/v2/closeTimingList` | — | — | deviceId, timingIds | **已禁用**；替代：`api/token/device/feederpro/closeTimingList`。设备 ID(推断) |
| 删除定时任务 | `api/token/device/feeder/v2/delTiming` | — | — | deviceId, timingId | 设备 ID(推断) |
| 干燥剂重置 | `api/token/device/feeder/v2/desiccant/reset` | — | — | deviceId | 设备 ID(推断) |
| 出粮(手动喂食) | `api/token/device/feeder/v2/foodOut` | — | — | deviceId, foodOutNum | `foodOutNum` 份数 1–10 |
| 童锁开关 | `api/token/device/feeder/v2/keyLock/setting` | — | — | deviceId, lockStatus | `lockStatus`=`true/false` |
| 安全锁 PIN | `api/token/device/feeder/v2/modifySec` | deviceId, signCode, oldSignCode | — | — | signCode/oldSignCode 为 4 位 PIN 的 SHA-256 小写十六进制(RSAUtils.sha256,勿传明文 PIN) |
| 喂食计划 | `api/token/device/feeder/v2/plan/updateListV2` | — | — | deviceId, planString | JSON 字符串 |
| 重新校准 | `api/token/device/feeder/v2/recalibration` | deviceId | — | — | 仅需 `deviceId` |
| 重命名 | `api/token/device/feeder/v2/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/device/feeder/v2/reset` | deviceId | — | — | 仅需 `deviceId` |
| 安全锁 PIN | `api/token/device/feeder/v2/setSec` | deviceId, signCode | — | — | signCode/oldSignCode 为 4 位 PIN 的 SHA-256 小写十六进制(RSAUtils.sha256,勿传明文 PIN) |
| 切换喂食模式 | `api/token/device/feeder/v2/switchMode` | deviceId, runModel | timingSetting, maxFood, foodOutCount, foodBalance, nums, maxNums, newDiet | — | JSON 字符串:`{hour,min,num,enable}` |
| 定时任务开关 | `api/token/device/feeder/v2/timingToggle` | — | — | deviceId, timingId, enable | `true` / `false`(推断) |
| 定时任务列表 | `api/token/device/feeder/v2/timings` | — | — | deviceId | 设备 ID(推断) |
| 解绑设备 | `api/token/device/feeder/v2/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 修改定时任务 | `api/token/device/feeder/v2/updTiming` | — | — | deviceId, timingSetting, timingId | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);查询返回的 JSON 对象不可直接作为写入载荷 |
| 安全锁 PIN | `api/token/device/feeder/v2/verifySec` | deviceId, signCode | — | — | signCode/oldSignCode 为 4 位 PIN 的 SHA-256 小写十六进制(RSAUtils.sha256,勿传明文 PIN) |
| remove | `api/token/device/feeder/stats/log/remove` | — | — | deviceId, logTypeAndIds | (推断) |
| modifyData | `api/token/device/feeder/stats/modifyData` | — | — | deviceId, logId, petId | 宠物 ID(推断) |
| getRecalibrationResult | `api/token/device/feeder/v2/getRecalibrationResult` | deviceId | — | — | 仅需 `deviceId` |
| sendCatFaceModelingCmd | `api/token/device/feeder/v2/sendCatFaceModelingCmd` | — | — | petId, deviceId | 宠物 ID(推断) |
| sleepMode | `api/token/device/feeder/v2/sleepMode` | — | — | deviceId, switchFlag | `true` / `false`(推断) |

### FEEDER_PRO 喂食器 Pro（36）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 新增定时任务 | `api/token/device/feederpro/addTiming` | deviceId, timingSetting | groupId | — | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);查询返回的 JSON 对象不可直接作为写入载荷 |
| 新增定时任务 | `api/token/device/feederpro/addTiming/v2` | deviceId, timingSetting | groupId | — | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);查询返回的 JSON 对象不可直接作为写入载荷 |
| 绑定设备 | `api/token/device/feederpro/bind` | — | — | mac | 仅需 `deviceId` |
| 绑定设备 | `api/token/device/feederpro/cat/bind` | deviceId, petId | collarsCode | — | 仅需 `deviceId` |
| 解绑设备 | `api/token/device/feederpro/cat/unbind` | deviceId, petId | — | — | 仅需 `deviceId` |
| 批量关闭/删除定时 | `api/token/device/feederpro/closeTimingList` | — | — | deviceId, timingIds | 设备 ID(推断) |
| 删除定时任务 | `api/token/device/feederpro/delTiming` | — | — | deviceId, timingId | 设备 ID(推断) |
| 批量关闭/删除定时 | `api/token/device/feederpro/deleteTimingList` | — | — | deviceId, timingIds | 设备 ID(推断) |
| 干燥剂重置 | `api/token/device/feederpro/desiccant/reset` | — | — | deviceId | 设备 ID(推断) |
| 固件升级 | `api/token/device/feederpro/firmware/update` | deviceId, version | — | — | 仅需 `deviceId` |
| 定时模式限粮 | `api/token/device/feederpro/foodLimitInTimingModel` | — | — | deviceId, foodLimitInTimingModel | 设备 ID(推断) |
| 童锁开关 | `api/token/device/feederpro/keyLock/setting` | — | — | deviceId, lockStatus | `lockStatus`=`true/false` |
| 夜间模式 | `api/token/device/feederpro/nightmode` | deviceId, switchFlag, startTime, endTime | — | — | 仅需 `deviceId` |
| 喂食计划 | `api/token/device/feederpro/plan/enable` | — | — | deviceId | 设备 ID(推断) |
| 喂食计划 | `api/token/device/feederpro/plan/switchPlanForToday` | — | — | deviceId, planId, copies, switchFlag | `true` / `false`(推断) |
| 重新校准 | `api/token/device/feederpro/recalibration` | deviceId | — | — | 仅需 `deviceId` |
| 重命名 | `api/token/device/feederpro/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/device/feederpro/reset` | deviceId | — | — | 仅需 `deviceId` |
| 回零校准 | `api/token/device/feederpro/return2Zero` | — | — | deviceId | 设备 ID(推断) |
| 切换食盆 | `api/token/device/feederpro/switchBowl` | — | — | deviceId, swithFlag | 设备 ID(推断) |
| 切换喂食模式 | `api/token/device/feederpro/switchMode/v2` | deviceId, feederproRunMode | timingSetting, maxFood, foodOutCount, foodBalance | — | JSON 字符串:`{hour,min,num,enable}` |
| 切换喂食模式 | `api/token/device/feederpro/switchModeForFeeder3` | deviceId, feederproRunMode | timingSetting | — | JSON 字符串:`{hour,min,num,enable}` |
| 定时任务开关 | `api/token/device/feederpro/timingToggle` | — | — | deviceId, timingId, enable | `true` / `false`(推断) |
| 定时任务列表 | `api/token/device/feederpro/timings` | — | — | deviceId | 设备 ID(推断) |
| 解绑设备 | `api/token/device/feederpro/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 修改定时任务 | `api/token/device/feederpro/updTiming` | — | — | deviceId, timingSetting, timingId | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);查询返回的 JSON 对象不可直接作为写入载荷 |
| 修改定时任务 | `api/token/device/feederpro/updTiming/v2` | — | — | deviceId, timingSetting, timingId | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);查询返回的 JSON 对象不可直接作为写入载荷 |
| 出粮(手动喂食) | `api/token/device/feederpro/v2/foodOut` | — | — | deviceId, foodOutNum | `foodOutNum` 份数 1–5 |
| allTimingToggle | `api/token/device/feederpro/allTimingToggle` | — | — | deviceId, enable | `true` / `false`(推断) |
| getRecalibrationResult | `api/token/device/feederpro/getRecalibrationResult` | deviceId | — | — | 仅需 `deviceId` |
| remove | `api/token/device/feederpro/stats/log/remove` | — | — | deviceId, logTypeAndIds | (推断) |
| modifyData | `api/token/device/feederpro/stats/modifyData` | — | — | deviceId, logId, petId | 宠物 ID(推断) |
| 声音设置 | `api/token/feederpro/sound/soundDelete` | — | — | deviceId, soundId | (推断) |
| 声音设置 | `api/token/feederpro/sound/soundPreview` | — | — | deviceId, id | (推断) |
| 声音设置 | `api/token/feederpro/sound/soundSwitch` | — | — | deviceId, id | (推断) |
| 声音设置 | `api/token/feederpro/sound/uploadFile` | — | — | file, deviceId, filename | — |

### F05 摄像头喂食器（36）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 新增定时任务 | `api/token/cameraFeeder/addTiming` | deviceId, timingSetting | groupId | — | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);无独立 `repeat` |
| 绑定设备 | `api/token/cameraFeeder/bind` | — | — | mac, deviceSerial, validateCode, deviceModel, deviceType, timezoneId | 待定 |
| 摄像头开关 | `api/token/cameraFeeder/cameraSwitch` | — | — | deviceId, cameraSwitch | 设备 ID(推断) |
| 绑定设备 | `api/token/cameraFeeder/cat/bind` | — | — | deviceId, petId | 猫咪/宠物 ID(推断) |
| 解绑设备 | `api/token/cameraFeeder/cat/unbind` | — | — | deviceId, petId | 猫咪/宠物 ID(推断) |
| 声音设置 | `api/token/cameraFeeder/chooseSound` | — | — | deviceId, soundId, enable | `true` / `false`(推断) |
| 删除定时任务 | `api/token/cameraFeeder/delTiming` | — | — | deviceId, timingId | 设备 ID(推断) |
| 固件升级 | `api/token/cameraFeeder/firmware/updateStatus` | — | — | deviceId, module | 设备 ID(推断) |
| 出粮(手动喂食) | `api/token/cameraFeeder/foodOut` | — | — | deviceId, foodOutNum | `foodOutNum` 份数 |
| 指示灯 | `api/token/cameraFeeder/indicatorSetting` | — | — | deviceId, status | 枚举字符串 |
| 童锁开关 | `api/token/cameraFeeder/keyLock/setting` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 声音设置 | `api/token/cameraFeeder/micSwitch` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 夜间模式 | `api/token/cameraFeeder/nightmode` | — | — | deviceId, switchFlag, startTime, endTime | `true` / `false`(推断) |
| 通知开关 | `api/token/cameraFeeder/noticeConfig/set` | — | — | deviceId, noticeItem, noticeSwitch | 通知项枚举 |
| 喂食计划 | `api/token/cameraFeeder/plan/switchPlanForToday` | — | — | deviceId, planId, switchFlag | `true` / `false`(推断) |
| 喂食计划 | `api/token/cameraFeeder/plan/update` | — | — | deviceId, petId, copies | 猫咪/宠物 ID(推断) |
| 重命名 | `api/token/cameraFeeder/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/cameraFeeder/reset` | deviceId | — | — | 仅需 `deviceId` |
| 定时任务开关 | `api/token/cameraFeeder/timingToggle` | — | — | deviceId, timingId, enable | `true` / `false`(推断) |
| 定时任务列表 | `api/token/cameraFeeder/timings` | — | — | deviceId | 设备 ID(推断) |
| 解绑设备 | `api/token/cameraFeeder/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 修改定时任务 | `api/token/cameraFeeder/updTiming` | — | — | deviceId, timingSetting, timingId | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);无独立 `repeat` |
| autoSwitch | `api/token/cameraFeeder/autoSwitch` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| balanceLimit | `api/token/cameraFeeder/balanceLimit` | deviceId, foodBalanceSwitch, foodBalanceLevel | — | — | (推断) |
| balanceLimitSwitch | `api/token/cameraFeeder/balanceLimitSwitch` | — | — | deviceId, enable | `true` / `false`(推断) |
| dailyRefillSetting | `api/token/cameraFeeder/dailyRefillSetting` | — | — | deviceId, copies | (推断) |
| faceModeSwitch | `api/token/cameraFeeder/faceModeSwitch` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| faceRecordStart | `api/token/cameraFeeder/faceRecordStart` | — | — | deviceId, petId | 宠物 ID(推断) |
| 固件 | `api/token/cameraFeeder/firmware/doUpdate` | — | — | deviceId, module | (推断) |
| foodoutTimeInterval | `api/token/cameraFeeder/foodoutTimeInterval` | — | — | deviceId, timeInterval, switchFlag | `true` / `false`(推断) |
| refillSetting | `api/token/cameraFeeder/refillSetting` | — | — | deviceId, copies | (推断) |
| 声音设置 | `api/token/cameraFeeder/soundDelete` | — | — | deviceId, soundId | (推断) |
| 声音设置 | `api/token/cameraFeeder/soundPreview` | — | — | deviceId, id | (推断) |
| submitSoundFile | `api/token/cameraFeeder/submitSoundFile` | — | — | deviceId, fileUploadId | (推断) |
| timerSwitch | `api/token/cameraFeeder/timerSwitch` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| voiceSetting | `api/token/cameraFeeder/voiceSetting` | — | — | deviceId, status | 枚举(推断) |

### VISUAL_FEEDER（16）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 新增定时任务 | `api/token/visualFeeder/addTiming` | deviceId, timingSetting | groupId | — | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);无独立 `repeat` |
| 删除定时任务 | `api/token/visualFeeder/delTiming` | — | — | deviceId, timingId | 设备 ID(推断) |
| 干燥剂重置 | `api/token/visualFeeder/desiccant/reset` | — | — | deviceId | 设备 ID(推断) |
| 出粮(手动喂食) | `api/token/visualFeeder/foodOut` | — | — | deviceId, foodOutNum | `foodOutNum` 份数 |
| 童锁开关 | `api/token/visualFeeder/keyLock/setting` | — | — | deviceId, lockStatus | `lockStatus`=`true/false` |
| 夜间模式 | `api/token/visualFeeder/nightmode` | deviceId, switchFlag, startTime, endTime | — | — | `HH:mm-HH:mm` |
| 喂食计划 | `api/token/visualFeeder/plan/updateCopies` | — | — | deviceId, planString | JSON 字符串 |
| 重命名 | `api/token/visualFeeder/rename` | — | — | deviceId, deviceName | 设备名称 |
| 切换喂食模式 | `api/token/visualFeeder/switchMode` | — | — | deviceId, runModel | 枚举编码(按机型)(推断) |
| 定时任务开关 | `api/token/visualFeeder/timingToggle` | — | — | deviceId, timingId, enable | `true` / `false`(推断) |
| 定时任务列表 | `api/token/visualFeeder/timings` | — | — | deviceId | 设备 ID(推断) |
| 修改定时任务 | `api/token/visualFeeder/updTiming` | — | — | deviceId, timingSetting, timingId | **写入** `timingSetting`=`HH:mm-份数-星期串`(分隔符 `-`);无独立 `repeat` |
| currentSchedule | `api/token/visualFeeder/currentSchedule` | — | — | deviceId | 仅需 `deviceId` |
| schedulePause | `api/token/visualFeeder/schedulePause` | — | — | deviceId, switchFlag, timingId | `true` / `false`(推断) |
| 声音设置 ❌服务端404 → 用 `api/token/feederpro/sound/soundDelete` | `api/token/visualFeeder/sound/soundDelete` | — | — | deviceId, soundId | **已禁用**；替代：`api/token/feederpro/sound/soundDelete`。(推断) |
| 声音设置 ❌服务端404 → 用 `api/token/feederpro/sound/uploadFile` | `api/token/visualFeeder/sound/uploadFile` | — | — | file, deviceId | **已禁用**；替代：`api/token/feederpro/sound/uploadFile`。— |

### PURE 饮水机（6）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 绑定设备 | `api/token/device/pure/bind` | — | — | mac | 仅需 `deviceId` |
| defaultToggle | `api/token/device/pure/defaultToggle` | — | — | deviceId, defaultStatus | `true` / `false`(推断) |
| defaultVoice | `api/token/device/pure/defaultVoice` | — | — | deviceId, defaultVoice | 设备 ID(推断) |
| 固件升级 | `api/token/device/pure/firmware/update` | deviceId, version | — | — | 固件版本号 |
| 解绑设备 | `api/token/device/pure/unbind` | deviceId | — | — | 仅需 `deviceId` |
| remove | `api/token/device/pure/stats/log/remove` | — | — | deviceId, logTypeAndIds | (推断) |

### PUREPRO 饮水机（17）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 绑定设备 | `api/token/device/purepro/bind` | — | — | mac | 仅需 `deviceId` |
| 绑定设备 | `api/token/device/purepro/cat/bind` | deviceId, petId | collarsCode | — | 猫咪/宠物 ID(推断) |
| 解绑设备 | `api/token/device/purepro/cat/unbind` | deviceId, petId | — | — | 猫咪/宠物 ID(推断) |
| 滤芯复位 | `api/token/device/purepro/filterElement/reset` | — | — | deviceId | 无参复位 |
| 固件升级 | `api/token/device/purepro/firmware/update` | — | — | deviceId, version | 固件版本号 |
| 浮毛模式 | `api/token/device/purepro/fluffyHair` | deviceId | — | — | 仅需 `deviceId` |
| 童锁开关 | `api/token/device/purepro/keyLock/setting` | — | — | deviceId, lockStatus | `lockStatus`=`true/false` |
| 按键音开关 | `api/token/device/purepro/keyTone/setting` | — | — | deviceId, lockStatus | `00`=解锁 / `01`=上锁 |
| 夜间模式 | `api/token/device/purepro/nightmode` | deviceId, switchFlag, startTime, endTime | — | — | `HH:mm-HH:mm` |
| 夜间模式 | `api/token/device/purepro/nightmodeV2` | deviceId, level, startTime, endTime, switchFlag | — | — | 仅需 `deviceId` |
| 重命名 | `api/token/device/purepro/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/device/purepro/reset` | deviceId | — | — | 仅需 `deviceId` |
| 设置出水模式 | `api/token/device/purepro/runMode` | — | — | deviceId, runMode | `CONTINUOUS_SPRING`/`INTERMITTENT_SPRING`/`INDUCTION_SPRING`(回读 `INDUCTION_SPRING`) |
| 解绑设备 | `api/token/device/purepro/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 共享成员 | `api/token/device/purepro/sharers` | — | — | deviceId | 仅需 `deviceId` |
| modifyData | `api/token/device/purepro/stats/log/modifyData` | — | — | eventId, deviceId, petId | 宠物 ID(推断) |
| remove | `api/token/device/purepro/stats/log/remove` | — | — | deviceId, logTypeAndIds | (推断) |

### 空气净化器（23）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 灯光设置 | `api/token/airpurifier/atmosphereLight/setting` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 绑定设备 | `api/token/airpurifier/bind` | — | — | mac, deviceSerial, validateCode, deviceModel, deviceType, timezoneId | 待定 |
| 滤芯复位 | `api/token/airpurifier/filterReset` | — | — | deviceId | 设备 ID(推断) |
| 固件升级 | `api/token/airpurifier/firmware/updateStatus` | — | — | deviceId, module | 设备 ID(推断) |
| 童锁开关 | `api/token/airpurifier/keyLock/setting` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 联动配置 | `api/token/airpurifier/linkage/config/save` | purifierDeviceId, enabled, delayMinutes, runDuration, endAction | litterboxDevices | — | 仅需 `deviceId` |
| 模式切换 | `api/token/airpurifier/modelSwitch` | — | — | deviceId, model | 枚举编码(按机型)(推断) |
| 静音开关 | `api/token/airpurifier/muteSwitch/setting` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 夜间模式 | `api/token/airpurifier/nightmode` | — | — | deviceId, switchFlag, startTime, endTime | `true` / `false`(推断) |
| 通知开关 | `api/token/airpurifier/noticeConfig/set` | — | — | deviceId, noticeItem, noticeSwitch | 通知项枚举 |
| 等离子净化 | `api/token/airpurifier/plasmaPurification/setting` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 重命名 | `api/token/airpurifier/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/airpurifier/reset` | — | — | deviceId | 设备 ID(推断) |
| 运行状态设置 | `api/token/airpurifier/runStatus/setting` | — | — | deviceId, runStatus | 设备 ID(推断) |
| 定时关机 | `api/token/airpurifier/shutdownTimer` | deviceId, switchFlag | hours | — | `true` / `false`(推断) |
| 风速档位 | `api/token/airpurifier/speedLevel` | — | — | deviceId, speedLevel | 设备 ID(推断) |
| 解绑设备 | `api/token/airpurifier/unbind` | deviceId | — | — | 仅需 `deviceId` |
| UV 杀菌 | `api/token/airpurifier/uvSwitch` | — | — | deviceId, switchFlag | `true` / `false`(推断) |
| 固件 | `api/token/airpurifier/firmware/doUpdate` | — | — | deviceId, module | (推断) |
| 分享 | `api/token/airpurifier/preShare` | — | — | deviceId, targetMobileCode, targetMobile, targetEmail | — |
| 分享 | `api/token/airpurifier/share` | — | — | deviceId, targetMobile, targetEmail | — |
| 取消分享 | `api/token/airpurifier/shareDelete` | — | — | deviceId, sharerId | — |
| 共享成员 | `api/token/airpurifier/sharers` | — | — | deviceId | — |

### 智能项圈（10）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 项圈同步 | `api/token/device/collar/cmd/data/syncAction` | — | — | deviceId, message | 设备 ID(推断) |
| 项圈同步 | `api/token/device/collar/cmd/time/sync` | — | — | deviceId | 设备 ID(推断) |
| defaultToggle ❌服务端404 → 用 `api/token/device/defaultToggle` | `api/token/device/collar/defaultToggle` | — | — | deviceId, defaultStatus | **已禁用**；替代：`api/token/device/defaultToggle`。`true` / `false`(推断) |
| defaultVoice ❌服务端404 → 用 `api/token/device/defaultVoice` | `api/token/device/collar/defaultVoice` | — | — | deviceId, defaultVoice | **已禁用**；替代：`api/token/device/defaultVoice`。设备 ID(推断) |
| 固件升级 | `api/token/device/collar/firmware/update/report` | — | — | deviceId, firmwareId, result | 设备 ID(推断) |
| 重命名 | `api/token/device/collar/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/device/collar/reset` | deviceId | — | — | 仅需 `deviceId` |
| 固件 | `api/token/device/collar/firmware/version/cache` | — | — | deviceId, majorVersion, minorVersion | (推断) |
| timeLineForActions | `api/token/device/collar/timeLineForActions` | — | — | deviceId, petId | 宠物 ID(推断) |
| timeLineForEvents | `api/token/device/collar/timeLineForEvents` | — | — | deviceId, petId | 宠物 ID(推断) |

### 烘干箱（7）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 绑定设备 | `api/token/device/drybox/bind` | — | — | timeZoneId, model, mac, sn | 枚举编码(按机型)(推断) |
| 固件升级 | `api/token/device/drybox/firmware/update/report` | — | — | deviceId, firmwareVersion, firmwareId, result | 设备 ID(推断) |
| 重命名 | `api/token/device/drybox/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/device/drybox/reset` | deviceId | — | — | 仅需 `deviceId` |
| 解绑设备 | `api/token/device/drybox/unbind` | deviceId | — | — | 仅需 `deviceId` |
| report | `api/token/device/drybox/error/report` | — | — | deviceId, errorContent | (推断) |
| 固件 | `api/token/device/drybox/firmware/version/cache` | — | — | deviceId, majorVersion, minorVersion | (推断) |

### 加热器（14）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 绑定设备 | `api/token/device/heater/bind` | — | — | timeZoneId, model, mac, sn | 枚举编码(按机型)(推断) |
| 绑定设备 | `api/token/device/heater/bindOtherDevice` | — | — | heaterId, otherDeviceType, deviceId, otherDeviceMac | 设备 ID(推断) |
| 加热提醒 | `api/token/device/heater/heatAlert` | — | — | deviceId, heaterPushEnum | 设备 ID(推断) |
| 重命名 | `api/token/device/heater/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/device/heater/reset` | deviceId | — | — | 仅需 `deviceId` |
| 解绑设备 | `api/token/device/heater/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 绑定/解绑外设 | `api/token/device/heater/unbindOtherDevice` | — | — | heaterId, otherDeviceType, deviceId, otherDeviceMac | 设备 ID(推断) |
| 上报温度 | `api/token/device/heater/updateCurrentTemperature` | — | — | deviceId, temperature, light | 设备 ID(推断) |
| faultReport | `api/token/device/heater/faultReport` | — | — | deviceId, content | (推断) |
| listAllAvailableHeater | `api/token/device/heater/listAllAvailableHeater` | — | — | otherDeviceMac, otherDeviceType | (推断) |
| listAllAvailablePure | `api/token/device/heater/listAllAvailablePure` | — | — | deviceId | 仅需 `deviceId` |
| listTemperatureLog | `api/token/device/heater/listTemperatureLog` | — | — | deviceId | 仅需 `deviceId` |
| report | `api/token/device/heater/update/report` | — | — | deviceId, firmwareVersion, firmwareId, result | (推断) |
| cache | `api/token/device/heater/version/cache` | — | — | deviceId, majorVersion, minorVersion | (推断) |

### 摄像头（4）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| defaultToggle | `api/token/device/camera/defaultToggle` | — | — | deviceId, defaultStatus | `true` / `false`(推断) |
| 解绑设备 | `api/token/device/camera/unbind` | deviceId | — | — | 仅需 `deviceId` |
| accessToken | `api/token/device/camera/accessToken` | — | — | — | — |
| assign | `api/token/device/camera/region/assign` | — | — | — | — |

### 摄像头 Pro（13）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 绑定设备 | `api/token/device/camerapro/bind` | — | — | mac, uid, authName, authPwd | 待定 |
| 重命名 | `api/token/device/camerapro/rename` | — | — | deviceId, deviceName | 设备名称 |
| 恢复出厂 | `api/token/device/camerapro/reset` | deviceId | — | — | 仅需 `deviceId` |
| 解绑设备 | `api/token/device/camerapro/unbind` | deviceId | — | — | 仅需 `deviceId` |
| 上报固件版本 | `api/token/device/camerapro/updateFirmwareVersion` | — | — | deviceId, version | 固件版本号 |
| activeDeviceCloudAuth | `api/token/device/camerapro/activeDeviceCloudAuth` | — | — | deviceId | 仅需 `deviceId` |
| getCloudPayUrl | `api/token/device/camerapro/getCloudPayUrl` | — | — | language, deviceName, mac, country, osType | 名称(推断) |
| getCloudVideoDownUrl | `api/token/device/camerapro/getCloudVideoDownUrl` | — | — | deviceId, startTime | (推断) |
| getCloudVideoPlayUrl | `api/token/device/camerapro/getCloudVideoPlayUrl` | — | — | deviceId, startTime | (推断) |
| getFirmwareUrl | `api/token/device/camerapro/getFirmwareUrl` | deviceId | sysVersion, appVersion, machineTypeName | — | (推断) |
| getMediaUrl | `api/token/device/camerapro/getMediaUrl` | — | — | deviceId, mediaId | (推断) |
| netFlowProtection | `api/token/device/camerapro/netFlowProtection` | — | — | deviceId, enable | `true` / `false`(推断) |
| preBind | `api/token/device/camerapro/preBind` | — | — | — | — |

### 猫砂盆伴侣（1）

| 操作 | 端点 | 必填参数 | 可选参数 | 未核实参数 | 取值／备注 |
|---|---|---|---|---|---|
| 绑定设备 | `api/token/device/wecare/bind` | — | — | mac | 仅需 `deviceId` |

<!-- operations:end -->
