#!/usr/bin/env python3
import requests
from datetime import datetime
import time
# 原来监控脚本，不要动！
# 店铺配置
STORES = {
    # "彩虹城玖都公馆": {
    #     "url": "https://www.huhhothome.cn/api/dynamicapi/apiview/viewdata?application=jqHj7ddxI1smOEkmKSD&apiview=house&_localversion=false&domainId=LAMDyAh4HSdnug1KdKL",
    #     "payload": {
    #         "lines": 10, "_currpage": 1, "status": "已上架", "houseType": "保障房",
    #         "houseEstateid": "6WD0LunYVjdwWfNbJyc"
    #     }
    # },
    "万锦店": {
        "url": "https://www.huhhothome.cn/api/dynamicapi/apiview/viewdata?application=jqHj7ddxI1smOEkmKSD&apiview=house&_localversion=false&domainId=LAMDyAh4HSdnug1KdKL",
        "payload": {
            "lines": 10, "_currpage": 1, "status": "已上架", "houseType": "保障房",
            "houseEstateid": "hB9zPAeL4ZI8r14ied4"
        }
    },
    "香林郡店": {
        "url": "https://www.huhhothome.cn/api/dynamicapi/apiview/viewdata?application=jqHj7ddxI1smOEkmKSD&apiview=house&_localversion=false&domainId=LAMDyAh4HSdnug1KdKL",
        "payload": {
            "lines": 10, "_currpage": 1, "status": "已上架", "houseType": "保障房",
            "houseEstateid": "7ZvBYfJp0A2n4GpjArv"
        }
    },
    "世源佳境店": {
        "url": "https://www.huhhothome.cn/api/dynamicapi/apiview/viewdata?application=jqHj7ddxI1smOEkmKSD&apiview=house&_localversion=false&domainId=LAMDyAh4HSdnug1KdKL",
        "payload": {
            "lines": 10, "_currpage": 1, "status": "已上架", "houseType": "保障房",
            "houseEstateid": "1cqOeivKdwdzhTFhjHx"
        }
    }
}

# 全局状态：记录每个店铺的通知状态（内存中）
NOTIFY_STATE = {}

# 配置
NOTIFY_REPEAT = 0        # 首次通知后，不再重复发送
COOL_DOWN_SECONDS = 3600 # 冷却时间：1小时 = 3600秒


def check_store(store_name, config):
    """检查店铺是否有房源"""
    try:
        response = requests.post(config["url"], json=config["payload"], timeout=8)
        data = response.json()

        if data.get("errcode") == 0 and data["data"]["rowcount"] > 0:
            houses = data["data"]["datas"]
            # 过滤掉小于50平的房源
            valid_houses = [h for h in houses if h["itemmap"].get("area", 0) >= 50]

            # 如果没有有效房源，返回False
            if len(valid_houses) == 0:
                return False, 0, ""
            # 统计面积分布
            area_80 = sum(1 for h in valid_houses if h["itemmap"].get("area", 0) >= 80)
            area_50 = sum(1 for h in valid_houses if 50 <= h["itemmap"].get("area", 0) < 80)
            area_other = len(houses) - area_80 - area_50

            area_parts = []
            if area_80 > 0:
                area_parts.append(f"{area_80}套80平")
            if area_50 > 0:
                area_parts.append(f"{area_50}套50平")
            if area_other > 0:
                # print(f"小于50平的{area_other}套丢弃")
                area_parts.append(f"小于50平{area_other}套")

            area_desc = "，".join(area_parts)

            return True, len(houses), area_desc
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 请求 {store_name} 出错: {e}")
        return False, 0, ""

    return False, 0, ""


def should_send_notification(store_name):
    """判断是否应该发送通知"""
    now = time.time()
    if store_name not in NOTIFY_STATE:
        # 第一次发现房源
        NOTIFY_STATE[store_name] = {
            "last_notify_time": now,
            "notify_count": 1
        }
        return True

    last_time = NOTIFY_STATE[store_name]["last_notify_time"]
    notify_count = NOTIFY_STATE[store_name]["notify_count"]

    # 是否还在冷却期？
    if now - last_time < COOL_DOWN_SECONDS:
        if notify_count <= NOTIFY_REPEAT:
            # 还在重复发送阶段（最多重复2次）
            NOTIFY_STATE[store_name]["notify_count"] += 1
            NOTIFY_STATE[store_name]["last_notify_time"] = now
            return True
        else:
            # 超过重复次数，进入冷却
            return False
    else:
        # 冷却期已过，可以重新开始
        NOTIFY_STATE[store_name] = {
            "last_notify_time": now,
            "notify_count": 1
        }
        return True


def send_notification(store_name, total, area_desc):
    """发送通知"""
    message = {
        "key1": f"{store_name}有新房源",
        "key2": f"{total}套房，{area_desc}",
        "key3": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    try:
        print(f"发送通知: {message}")
        # 取消注释以启用真实通知

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 发送通知失败: {e}")


def main():
    """主循环：每5秒检查一次所有店铺"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 房源监控启动，每5秒检查一次...")

    while True:
        for store, config in STORES.items():
            has_house, total, area_desc = check_store(store, config)
            if has_house:
                if should_send_notification(store):
                    send_notification(store, total, area_desc)
                else:
                    # 可选：打印静默丢弃日志
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {store} 有房但处于冷却期，跳过通知")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {store} 无房")

        time.sleep(5)  # 每5秒检查一次


if __name__ == "__main__":
    main()