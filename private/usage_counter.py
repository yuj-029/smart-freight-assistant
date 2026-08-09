"""
免费用量计数器 - 盯箱/截关/运价波动的每日免费额度管理

规则：
- 盯箱：3 个活跃 B/L 号
- 截关查询：5 次/天（次日 0 点重置）
- 单证提醒：3 条/天（次日 0 点重置）
- 运价波动：3 条航线订阅
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_FILE = DATA_DIR / "usage.json"

FREE_LIMITS = {
    "tracking_active": 3,       # 盯箱活跃监控数
    "cutoff_query": 5,          # 截关查询次数/天
    "doc_reminder": 3,          # 单证提醒条数/天
    "price_alert_routes": 3,    # 运价波动订阅航线数
}

BYPASS_MODE = True  # True=跳过所有额度限制，False=正常计数


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> Dict:
    _ensure_data_dir()
    if not DATA_FILE.exists():
        return _init_empty()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: Dict):
    _ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _init_empty() -> Dict:
    return {
        "tracking": {"active_ids": [], "max": FREE_LIMITS["tracking_active"]},
        "cutoff_query": {"date": "", "count": 0, "max": FREE_LIMITS["cutoff_query"]},
        "doc_reminder": {"date": "", "count": 0, "max": FREE_LIMITS["doc_reminder"]},
        "price_alert": {"routes": [], "max": FREE_LIMITS["price_alert_routes"]},
    }


def _reset_daily(data: Dict, key: str):
    """如果跨天了，重置日计数"""
    today = str(date.today())
    if data[key].get("date") != today:
        data[key]["date"] = today
        data[key]["count"] = 0


def check_tracking_can_add(bill_id: str) -> Dict:
    """检查是否可以添加盯箱监控"""
    if BYPASS_MODE:
        return {"allowed": True, "action": "bypass", "current": 0, "max": 999}
    data = _load()
    active = data["tracking"]["active_ids"]
    if bill_id in active:
        return {"allowed": True, "action": "already_tracking", "current": len(active), "max": FREE_LIMITS["tracking_active"]}
    if len(active) >= FREE_LIMITS["tracking_active"]:
        return {"allowed": False, "reason": f"已达免费上限 {FREE_LIMITS['tracking_active']} 个活跃监控，请先清理闲置项", "current": len(active), "max": FREE_LIMITS["tracking_active"]}
    return {"allowed": True, "action": "add", "current": len(active), "max": FREE_LIMITS["tracking_active"]}


def add_tracking(bill_id: str) -> bool:
    """添加盯箱监控"""
    result = check_tracking_can_add(bill_id)
    if not result["allowed"]:
        return False
    if result.get("action") == "already_tracking":
        return True
    data = _load()
    data["tracking"]["active_ids"].append(bill_id)
    _save(data)
    return True


def remove_tracking(bill_id: str):
    """移除盯箱监控"""
    data = _load()
    if bill_id in data["tracking"]["active_ids"]:
        data["tracking"]["active_ids"].remove(bill_id)
        _save(data)


def get_tracking_list() -> List[str]:
    """获取当前活跃监控列表"""
    data = _load()
    return data["tracking"]["active_ids"]


def check_and_consume_cutoff() -> Dict:
    """检查截关查询额度，允许则消耗1次"""
    if BYPASS_MODE:
        return {"allowed": True, "used": 0, "remaining": 999, "max": 999}
    data = _load()
    _reset_daily(data, "cutoff_query")
    if data["cutoff_query"]["count"] >= FREE_LIMITS["cutoff_query"]:
        _save(data)
        return {"allowed": False, "reason": f"今日截关查询已达上限 {FREE_LIMITS['cutoff_query']} 次，请明天再试", "used": data["cutoff_query"]["count"], "max": FREE_LIMITS["cutoff_query"]}
    data["cutoff_query"]["count"] += 1
    _save(data)
    return {"allowed": True, "used": data["cutoff_query"]["count"], "remaining": FREE_LIMITS["cutoff_query"] - data["cutoff_query"]["count"], "max": FREE_LIMITS["cutoff_query"]}


def check_and_consume_doc_reminder() -> Dict:
    """检查单证提醒额度，允许则消耗1条"""
    if BYPASS_MODE:
        return {"allowed": True, "used": 0, "remaining": 999, "max": 999}
    data = _load()
    _reset_daily(data, "doc_reminder")
    if data["doc_reminder"]["count"] >= FREE_LIMITS["doc_reminder"]:
        _save(data)
        return {"allowed": False, "reason": f"今日单证提醒已达上限 {FREE_LIMITS['doc_reminder']} 条，请明天再试", "used": data["doc_reminder"]["count"], "max": FREE_LIMITS["doc_reminder"]}
    data["doc_reminder"]["count"] += 1
    _save(data)
    return {"allowed": True, "used": data["doc_reminder"]["count"], "remaining": FREE_LIMITS["doc_reminder"] - data["doc_reminder"]["count"], "max": FREE_LIMITS["doc_reminder"]}


def check_price_alert_can_add(route: str) -> Dict:
    """检查是否可以添加运价波动订阅"""
    if BYPASS_MODE:
        return {"allowed": True, "action": "bypass", "current": 0, "max": 999}
    data = _load()
    routes = data["price_alert"]["routes"]
    if route in routes:
        return {"allowed": True, "action": "already_subscribed", "current": len(routes), "max": FREE_LIMITS["price_alert_routes"]}
    if len(routes) >= FREE_LIMITS["price_alert_routes"]:
        return {"allowed": False, "reason": f"已达免费上限 {FREE_LIMITS['price_alert_routes']} 条航线，请先取消不关注的航线", "current": len(routes), "max": FREE_LIMITS["price_alert_routes"]}
    return {"allowed": True, "action": "add", "current": len(routes), "max": FREE_LIMITS["price_alert_routes"]}


def add_price_alert_route(route: str) -> bool:
    """添加运价波动订阅"""
    result = check_price_alert_can_add(route)
    if not result["allowed"]:
        return False
    if result.get("action") == "already_subscribed":
        return True
    data = _load()
    data["price_alert"]["routes"].append(route)
    _save(data)
    return True


def remove_price_alert_route(route: str):
    """取消运价波动订阅"""
    data = _load()
    if route in data["price_alert"]["routes"]:
        data["price_alert"]["routes"].remove(route)
        _save(data)


def get_price_alert_routes() -> List[str]:
    return _load()["price_alert"]["routes"]


def get_usage_summary() -> Dict:
    """获取所有用量概览"""
    data = _load()
    _reset_daily(data, "cutoff_query")
    _reset_daily(data, "doc_reminder")
    return {
        "tracking": {"active": len(data["tracking"]["active_ids"]), "max": FREE_LIMITS["tracking_active"], "ids": data["tracking"]["active_ids"]},
        "cutoff_query": {"used": data["cutoff_query"]["count"], "max": FREE_LIMITS["cutoff_query"]},
        "doc_reminder": {"used": data["doc_reminder"]["count"], "max": FREE_LIMITS["doc_reminder"]},
        "price_alert": {"active": len(data["price_alert"]["routes"]), "max": FREE_LIMITS["price_alert_routes"], "routes": data["price_alert"]["routes"]},
    }


def check_usage_warnings() -> List[Dict]:
    """
    检查所有模块的免费额度使用情况，接近上限时返回预警。

    Returns: [{"module": "cutoff_query", "used": 4, "max": 5, "pct": 80, "warning": "..."}, ...]
    """
    summary = get_usage_summary()
    warnings = []

    # 盯箱预警（>= 2/3 时提醒）
    tracking = summary["tracking"]
    if tracking["active"] >= tracking["max"] - 1 and tracking["active"] < tracking["max"]:
        warnings.append({
            "module": "tracking",
            "used": tracking["active"],
            "max": tracking["max"],
            "pct": round(tracking["active"] / tracking["max"] * 100),
            "warning": f"盯箱已用 {tracking['active']}/{tracking['max']}，即将达到上限",
        })
    elif tracking["active"] >= tracking["max"]:
        warnings.append({
            "module": "tracking",
            "used": tracking["active"],
            "max": tracking["max"],
            "pct": 100,
            "warning": f"盯箱已满 {tracking['active']}/{tracking['max']}，请清理闲置项",
        })

    # 截关查询预警（>= 4/5 时提醒）
    cq = summary["cutoff_query"]
    if cq["max"] - cq["used"] <= 2 and cq["used"] < cq["max"]:
        warnings.append({
            "module": "cutoff_query",
            "used": cq["used"],
            "max": cq["max"],
            "pct": round(cq["used"] / cq["max"] * 100),
            "warning": f"截关查询已用 {cq['used']}/{cq['max']} 次，今日还剩 {cq['max'] - cq['used']} 次",
        })
    elif cq["used"] >= cq["max"]:
        warnings.append({
            "module": "cutoff_query",
            "used": cq["used"],
            "max": cq["max"],
            "pct": 100,
            "warning": f"截关查询今日已用完 {cq['max']} 次，请明天再试",
        })

    # 单证提醒预警
    dr = summary["doc_reminder"]
    if dr["used"] >= dr["max"]:
        warnings.append({
            "module": "doc_reminder",
            "used": dr["used"],
            "max": dr["max"],
            "pct": 100,
            "warning": f"单证提醒今日已用完 {dr['max']} 条，请明天再试",
        })

    # 运价波动预警（>= 2/3）
    pa = summary["price_alert"]
    if pa["active"] >= pa["max"] - 1 and pa["active"] < pa["max"]:
        warnings.append({
            "module": "price_alert",
            "used": pa["active"],
            "max": pa["max"],
            "pct": round(pa["active"] / pa["max"] * 100),
            "warning": f"运价订阅已用 {pa['active']}/{pa['max']}，即将达到上限",
        })
    elif pa["active"] >= pa["max"]:
        warnings.append({
            "module": "price_alert",
            "used": pa["active"],
            "max": pa["max"],
            "pct": 100,
            "warning": f"运价订阅已满 {pa['active']}/{pa['max']}，请取消不关注的航线",
        })

    return warnings


def format_usage_warnings() -> Optional[str]:
    """格式化免费期预警消息。无预警返回 None。"""
    warnings = check_usage_warnings()
    if not warnings:
        return None
    
    lines = ["⚠️ **免费额度预警**\n"]
    for w in warnings:
        lines.append(f"- {w['warning']}")
    return "\n".join(lines)
