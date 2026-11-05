#!/usr/bin/env python3
"""CATLINK 数据获取工具 - 主程序"""

import json
import os
from datetime import date

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

from catlink_client import CatLinkClient


def load_config():
    """从 .env 文件加载配置"""
    if HAS_DOTENV:
        load_dotenv()

    config = {
        "phone": os.getenv("CATLINK_PHONE", ""),
        "password": os.getenv("CATLINK_PASSWORD", ""),
        "phone_iac": os.getenv("CATLINK_PHONE_IAC", "86"),
        "region": os.getenv("CATLINK_REGION", "china"),
        "language": os.getenv("CATLINK_LANGUAGE", "zh_CN"),
    }

    return config


def mask_phone(phone: str) -> str:
    """脱敏手机号，避免日志中输出完整账号。"""
    if len(phone) <= 4:
        return "*" * len(phone)
    return f"{phone[:3]}****{phone[-4:]}"


def print_device_detail(device_type: str, client, device_id: str):
    """根据设备类型打印设备详情"""
    print(f"\n  正在获取设备详情...")

    if device_type == "PUREPRO":
        detail = client.purepro.get_detail(device_id)
        print("  水碗详情:", json.dumps(detail, ensure_ascii=False, indent=2))
        # 获取水碗记录
        print("\n  正在获取水碗记录 Top5...")
        logs = client.purepro.get_logs_top5(device_id)
        print("  水碗记录:", json.dumps(logs, ensure_ascii=False, indent=2))

    elif device_type == "FEEDER":
        detail = client.feeder.get_detail(device_id)
        print("  喂食器详情:", json.dumps(detail, ensure_ascii=False, indent=2))
        print("\n  正在获取出粮记录 Top5...")
        logs = client.feeder.get_logs_top5(device_id)
        print("  出粮记录:", json.dumps(logs, ensure_ascii=False, indent=2))

    elif device_type == "FEEDER_PRO":
        detail = client.feeder_pro.get_detail(device_id)
        print("  喂食器Pro详情:", json.dumps(detail, ensure_ascii=False, indent=2))
        print("\n  正在获取出粮记录 Top5...")
        logs = client.feeder_pro.get_logs_top5(device_id)
        print("  出粮记录:", json.dumps(logs, ensure_ascii=False, indent=2))
        print("\n  正在获取耗材列表...")
        consumable = client.feeder_pro.get_consumable_list(device_id)
        print("  耗材列表:", json.dumps(consumable, ensure_ascii=False, indent=2))

    elif device_type == "SCOOPER":
        detail = client.scooper.get_detail(device_id)
        print("  Scooper详情:", json.dumps(detail, ensure_ascii=False, indent=2))
        print("\n  正在获取记录 Top5...")
        logs = client.scooper.get_logs_top5(device_id)
        print("  记录:", json.dumps(logs, ensure_ascii=False, indent=2))

    elif device_type == "LITTER_BOX_599":
        detail = client.litter_box_599.get_detail(device_id)
        print("  LitterBox详情:", json.dumps(detail, ensure_ascii=False, indent=2))
        print("\n  正在获取记录 Top5...")
        logs = client.litter_box_599.get_logs_top5(device_id)
        print("  记录:", json.dumps(logs, ensure_ascii=False, indent=2))

    elif device_type == "VISUAL_PRO_ULTRA":
        detail = client.scooper_pro_ultra.get_detail(device_id)
        print("  ScooperProUltra详情:", json.dumps(detail, ensure_ascii=False, indent=2))
        print("\n  正在获取记录 Top5...")
        logs = client.scooper_pro_ultra.get_logs_top5(device_id)
        print("  记录:", json.dumps(logs, ensure_ascii=False, indent=2))

    elif device_type == "VISUAL_C07":
        detail = client.visual_c07.get_detail(device_id)
        print("  大白 Pro 状态:", detail.get("workStatus"))
        print("  累计清理次数:", detail.get("totalCleanTimes"))
        sand_info = client.visual_c07.get_sand_info(device_id)
        print("  补砂模块已安装:", sand_info.get("install"))

    elif device_type == "C08":
        detail = client.c08.get_detail(device_id)
        print("  C08详情:", json.dumps(detail, ensure_ascii=False, indent=2))
        print("\n  正在获取记录 Top5...")
        logs = client.c08.get_logs_top5(device_id)
        print("  记录:", json.dumps(logs, ensure_ascii=False, indent=2))
        print("\n  正在获取猫咪统计...")
        stats = client.c08.get_stats_cats(device_id)
        print("  猫咪统计:", json.dumps(stats, ensure_ascii=False, indent=2))

    else:
        # 未知设备类型，尝试通用接口
        detail = client.get_device_detail(device_id)
        detail_data = (detail.get("data") or {}).get("deviceInfo") or {}
        if detail_data:
            print("  设备详情:", json.dumps(detail_data, ensure_ascii=False, indent=2))


def main():
    """主程序"""
    print("=" * 50)
    print("CATLINK 数据获取工具")
    print("=" * 50)

    # 从 .env 加载配置
    config = load_config()
    phone = config["phone"]
    password = config["password"]
    phone_iac = config["phone_iac"]
    region = config["region"]
    language = config["language"]

    if not phone or not password:
        print("错误: 请在 .env 文件中配置 CATLINK_PHONE 和 CATLINK_PASSWORD")
        print("参考 .env.example 文件创建配置")
        return

    print(f"使用配置: 手机号={mask_phone(phone)}, 国家代码={phone_iac}, 区域={region}")

    # 创建客户端
    client = CatLinkClient(
        phone=phone,
        password=password,
        phone_iac=phone_iac,
        region=region,
        language=language,
    )

    # 登录
    print("\n正在登录...")
    if not client.login():
        print("登录失败，请检查账号密码！")
        return

    # 获取设备列表
    print("\n正在获取设备列表...")
    devices = client.get_devices()

    if devices:
        print(f"\n找到 {len(devices)} 个设备:")
        print("-" * 50)

        for idx, device in enumerate(devices, 1):
            print(f"\n【设备 {idx}】")
            print(f"  ID: {device.get('id')}")
            print(f"  MAC: {device.get('mac')}")
            print(f"  名称: {device.get('deviceName')}")
            print(f"  型号: {device.get('model')}")
            print(f"  类型: {device.get('deviceType')}")
            print(f"  错误: {device.get('currentErrorMessage')}")

            # 获取设备详情
            device_id = device.get("id")
            device_type = device.get("deviceType")
            if device_id:
                print_device_detail(device_type, client, device_id)
    else:
        print("未找到设备")

    # 获取猫咪列表
    print("\n" + "=" * 50)
    print("正在获取猫咪列表...")
    cats = client.cat.get_list("Asia/Shanghai")

    if cats:
        print(f"\n找到 {len(cats)} 只猫咪:")
        print("-" * 50)

        today = date.today().isoformat()
        for idx, cat in enumerate(cats, 1):
            print(f"\n【猫咪 {idx}】")
            print(f"  ID: {cat.get('id')}")
            print(f"  名字: {cat.get('petName')}")
            print(f"  品种: {cat.get('breedName')}")
            print(f"  性别: {cat.get('gender')}")
            print(f"  体重: {cat.get('weight')} kg")

            # 获取健康摘要
            pet_id = cat.get("id")
            if pet_id:
                print(f"\n  正在获取 {today} 的健康数据...")
                summary = client.cat.get_summary(pet_id, today, "Asia/Shanghai")
                if summary:
                    print(f"  如厕次数: {summary.get('toiletTimes')}")
                    print(f"  如厕时长: {summary.get('toiletDuration')} 秒")
                    print(f"  体重: {summary.get('weight')} kg")
                    print(f"  活动时长: {summary.get('sportDuration')} 秒")

    print("\n" + "=" * 50)
    print("完成！")


if __name__ == "__main__":
    main()
