"""
主动轮询骨架 - 定时调度盯箱/运价/截关的周期性检查

本模块为调度器入口，实际执行依赖外部触发（如 Marvis 定时任务 / cron / Windows 计划任务）。
提供统一的全量巡检函数供外部调度器调用。
"""

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

_PARENT = Path(__file__).parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))


def poll_all() -> Dict:
    """
    全量巡检入口。供外部定时调度器调用（如 Marvis 定时任务）。

    执行流程：
    1. 检查所有活跃盯箱的 AIS 状态 + 到港 + 异常
    2. 检查所有订阅航线的运价波动
    3. 检查截关倒计时（如果已录入）
    4. 检查免费额度预警

    Returns: {"polls": int, "alerts": int, "warnings": int, "errors": int}
    """
    stats = {"polls": 0, "alerts": 0, "warnings": 0, "errors": 0}

    # 1. 盯箱巡检
    # 注：实际 web_search 调用由 Marvis Agent 执行，poller.py 只负责生成查询指令和解析结果。
    # 返回的 stats["pending_web_searches"] 由 Agent 消费并调用 parse_web_search_result() 解析后缓存。
    try:
        from usage_counter import get_tracking_list
        from scrapers.tracking import (
            get_vessel_position, detect_anomalies,
            build_vessel_search_queries, parse_web_search_result
        )
        from arrival_alert import check_arrival, format_arrival_alert
        from alert_dispatcher import dispatch

        active_bills = get_tracking_list()
        pending_searches = []

        for bill_id in active_bills:
            stats["polls"] += 1
            # 尝试从缓存获取船位；无缓存时生成 web_search 指令
            pos = get_vessel_position(bill_id, source="web_search")

            if pos.get("mode") == "search_required":
                pending_searches.extend(pos["search_queries"])
                continue

            if "error" in pos:
                continue

            # 异常检测：AIS 信号丢失 / ETA 延误
            anomalies = detect_anomalies(bill_id)
            for a in anomalies:
                dispatch(
                    "tracking_delay" if "delay" in a["type"] else "tracking_signal_loss",
                    f"船期异常: {bill_id}",
                    a["message"],
                    dedup_key=f"anomaly:{bill_id}:{a['type']}"
                )
                stats["alerts"] += 1

            # 到港检查
            if pos.get("latitude") and pos.get("longitude") and pos.get("destination"):
                arrival = check_arrival(
                    bill_id,
                    pos["latitude"], pos["longitude"],
                    pos["destination"],
                    eta=pos.get("eta")
                )
                if arrival["should_alert"]:
                    msg = format_arrival_alert(arrival)
                    if msg:
                        dispatch("tracking_arrival", f"到港提醒: {bill_id}", msg,
                                 dedup_key=f"arrival:{bill_id}:{pos.get('eta', '')}")
                        stats["alerts"] += 1

        if pending_searches:
            stats["pending_web_searches"] = pending_searches
    except Exception as e:
        stats["errors"] += 1

    # 1.5. 集装箱追踪巡检
    # 注：实际 web_search 由 Marvis Agent 执行，本段只负责生成查询指令和基础异常检测。
    try:
        from usage_counter import get_tracking_list
        from scrapers.tracking import (
            build_container_search_queries, parse_container_search_result,
            get_container_status,
        )
        from alert_dispatcher import dispatch

        active_bills = get_tracking_list()
        container_pending = []
        for bill_id in active_bills:
            stats["polls"] += 1
            result = get_container_status(bill_id, source="web_search")
            if result.get("mode") == "search_required":
                container_pending.extend(result["search_queries"])
                continue
            if "error" in result:
                continue
            # 缓存命中：检查柜况异常（超 5 天无更新）
            last_update = result.get("last_update") or result.get("updated_at", "")
            if last_update:
                try:
                    ts = datetime.fromisoformat(
                        last_update.replace("Z", "+00:00").replace("T", " ")
                    )
                    age_days = (date.today() - ts.date()).days
                    if age_days >= 5:
                        dispatch(
                            "container_stale",
                            f"集装箱追踪过期: {bill_id}",
                            f"{bill_id} 最后更新于 {age_days} 天前，状态: {result.get('status', '未知')}",
                            dedup_key=f"container_stale:{bill_id}:{date.today()}",
                        )
                        stats["alerts"] += 1
                except (ValueError, TypeError):
                    pass
        if container_pending:
            if "pending_container_searches" not in stats:
                stats["pending_container_searches"] = []
            stats["pending_container_searches"].extend(container_pending)
    except Exception as e:
        stats["errors"] += 1

    # 2. 运价巡检
    try:
        from usage_counter import get_price_alert_routes
        from price_alert import get_route_status

        routes = get_price_alert_routes()
        for route in routes:
            stats["polls"] += 1
            status = get_route_status(route, "wci")
            if status.get("alert_triggered"):
                from price_alert import format_price_alert_report
                report = format_price_alert_report(route, "wci")
                dispatch("price_alert", f"运价波动: {route}", report,
                         dedup_key=f"price:{route}:{status.get('updated')}")
                stats["alerts"] += 1
    except Exception as e:
        stats["errors"] += 1

    # 3. 额度预警
    try:
        from usage_counter import format_usage_warnings
        warning_msg = format_usage_warnings()
        if warning_msg:
            dispatch("usage_warning", "免费额度预警", warning_msg,
                     dedup_key=f"usage:{date.today()}")
            stats["warnings"] += 1
    except Exception as e:
        stats["errors"] += 1

    return stats


def poll_tracking_only() -> Dict:
    """仅巡检盯箱模块。实际 web_search 由 Marvis Agent 执行。"""
    stats = {"polls": 0, "alerts": 0, "errors": 0}
    try:
        from usage_counter import get_tracking_list
        from scrapers.tracking import (
            get_vessel_position, detect_anomalies,
            build_vessel_search_queries, parse_web_search_result
        )
        from arrival_alert import check_arrival, format_arrival_alert
        from alert_dispatcher import dispatch

        active_bills = get_tracking_list()
        pending_searches = []

        for bill_id in active_bills:
            stats["polls"] += 1
            pos = get_vessel_position(bill_id, source="web_search")

            if pos.get("mode") == "search_required":
                pending_searches.extend(pos["search_queries"])
                continue

            if "error" in pos:
                continue

            anomalies = detect_anomalies(bill_id)
            for a in anomalies:
                dispatch(
                    "tracking_delay" if "delay" in a["type"] else "tracking_signal_loss",
                    f"船期异常: {bill_id}",
                    a["message"],
                    dedup_key=f"anomaly:{bill_id}:{a['type']}"
                )
                stats["alerts"] += 1

            if pos.get("latitude") and pos.get("longitude") and pos.get("destination"):
                arrival = check_arrival(
                    bill_id,
                    pos["latitude"], pos["longitude"],
                    pos["destination"],
                    eta=pos.get("eta")
                )
                if arrival["should_alert"]:
                    msg = format_arrival_alert(arrival)
                    if msg:
                        dispatch("tracking_arrival", f"到港提醒: {bill_id}", msg,
                                 dedup_key=f"arrival:{bill_id}:{pos.get('eta', '')}")
                        stats["alerts"] += 1

        if pending_searches:
            stats["pending_web_searches"] = pending_searches
    except Exception as e:
        stats["errors"] += 1
    return stats
