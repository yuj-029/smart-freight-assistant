"""
运价波动提醒 - 基于公开运价指数 (WCI / SCFI) 的航线价格追踪与阈值告警

数据源：
- Drewry WCI (World Container Index): 8条主干航线每周四更新
- SCFI (Shanghai Containerized Freight Index): 15条航线每周五更新

阈值触发：当前值较前值涨跌幅 ≥ 用户设定阈值（默认 ±5%）时推送告警
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"

EXCHANGE_RATE = 7.25  # 兜底汇率，实际应从一期汇率模块获取

# WCI 8条主干航线
WCI_ROUTES = {
    "shanghai-rotterdam": "上海 → 鹿特丹",
    "shanghai-genoa": "上海 → 热那亚",
    "shanghai-los_angeles": "上海 → 洛杉矶",
    "shanghai-new_york": "上海 → 纽约",
    "rotterdam-shanghai": "鹿特丹 → 上海",
    "rotterdam-new_york": "鹿特丹 → 纽约",
    "los_angeles-shanghai": "洛杉矶 → 上海",
    "new_york-rotterdam": "纽约 → 鹿特丹",
}

# SCFI 主要航线（前15条）
SCFI_ROUTES = {
    "shanghai-europe": "上海 → 欧洲基本港",
    "shanghai-mediterranean": "上海 → 地中海基本港",
    "shanghai-uswc": "上海 → 美西基本港",
    "shanghai-usec": "上海 → 美东基本港",
    "shanghai-persian_gulf": "上海 → 波斯湾",
    "shanghai-australia_nz": "上海 → 澳新",
    "shanghai-west_africa": "上海 → 西非",
    "shanghai-south_africa": "上海 → 南非",
    "shanghai-south_america": "上海 → 南美",
    "shanghai-japan_kansai": "上海 → 日本关西",
    "shanghai-japan_kanto": "上海 → 日本关东",
    "shanghai-se_asia": "上海 → 东南亚",
    "shanghai-korea": "上海 → 韩国",
    "shanghai-taiwan": "上海 → 台湾",
    "shanghai-hongkong": "上海 → 香港",
}

ALL_ROUTES = {**WCI_ROUTES, **SCFI_ROUTES}

INDEX_FILE = DATA_DIR / "price_index_cache.json"
ALERT_CONFIG_FILE = DATA_DIR / "price_alert_config.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_index_cache() -> Dict:
    _ensure_data_dir()
    if not INDEX_FILE.exists():
        return {}
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index_cache(data: Dict):
    _ensure_data_dir()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_alert_config() -> Dict:
    _ensure_data_dir()
    if not ALERT_CONFIG_FILE.exists():
        return {}
    with open(ALERT_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_alert_config(data: Dict):
    _ensure_data_dir()
    with open(ALERT_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_index(route_code: str, source: str, current_value: float, unit: str = "USD"):
    """
    更新指数缓存并检测是否需要告警。

    Args:
        route_code: 航线代码
        source: 'wci' 或 'scfi'
        current_value: 当前指数 / 运价
        unit: 币种（默认 USD）

    Returns:
        含涨跌幅 + 是否触发告警的字典
    """
    cache = _load_index_cache()
    key = f"{source}:{route_code}"
    previous = cache.get(key)
    today = str(date.today())

    entry = {
        "route": route_code,
        "route_name": ALL_ROUTES.get(route_code, route_code),
        "source": source.upper(),
        "value": current_value,
        "unit": unit,
        "updated": today,
    }

    change_pct = None
    triggered = False

    if previous and previous.get("value"):
        prev_val = previous["value"]
        if prev_val > 0:
            change_pct = round((current_value - prev_val) / prev_val * 100, 2)

    entry["previous_value"] = previous.get("value") if previous else None
    entry["change_pct"] = change_pct

    if change_pct is not None:
        alert_config = _load_alert_config()
        config = alert_config.get(route_code, {})
        threshold = config.get("threshold", 5.0)  # 默认 ±5%
        if abs(change_pct) >= threshold:
            direction = "📈 上涨" if change_pct > 0 else "📉 下跌"
            entry["alert_triggered"] = True
            entry["alert_direction"] = direction
            entry["alert_threshold"] = threshold
            triggered = True
        else:
            entry["alert_triggered"] = False
    else:
        entry["alert_triggered"] = False

    cache[key] = entry
    _save_index_cache(cache)
    return entry


def get_route_status(route_code: str, source: str = "wci") -> Dict:
    """查询指定航线最新指数状态。"""
    cache = _load_index_cache()
    key = f"{source}:{route_code}"
    entry = cache.get(key)
    if not entry:
        return {"error": f"暂无 {source.upper()} {route_code} 的缓存数据", "route": route_code}
    return entry


def set_alert_threshold(route_code: str, threshold_pct: float = 5.0):
    """设置航线波动告警阈值（百分比）。"""
    config = _load_alert_config()
    config[route_code] = {"threshold": threshold_pct, "updated": str(date.today())}
    _save_alert_config(config)


def get_alert_config(route_code: str) -> Dict:
    """查询航线告警配置。"""
    config = _load_alert_config()
    return config.get(route_code, {"threshold": 5.0, "note": "使用默认阈值 ±5%"})


def format_price_alert_report(route_code: str, source: str = "wci") -> str:
    """生成运价波动告警报告 Markdown 文本。"""
    status = get_route_status(route_code, source)
    if "error" in status:
        return f"⚠️ {status['error']}"

    value_rmb = round(status['value'] * EXCHANGE_RATE, 0)

    report = f"""## 📊 {status['route_name']}（{status['source']}）

| 指标 | 数值 |
|------|------|
| 当前指数 | {status['value']} {status['unit']} |
| 当前指数(RMB) | {value_rmb:.0f} CNY |
| 上次指数 | {status['previous_value'] or '—'} {status['unit']} |
| 涨跌幅 | {status['change_pct']:+.2f}% |
| 更新时间 | {status['updated']} |
"""

    if status.get("alert_triggered"):
        report += f"\n{status['alert_direction']} **{abs(status['change_pct'])}%**，超过阈值 {status['alert_threshold']}%"

    report += f"\n\n> 💱 参考汇率: 1 USD ≈ {EXCHANGE_RATE:.2f} CNY（BOC 卖出价，非实时请查最新）"

    return report


def list_available_routes() -> Dict[str, Dict]:
    """列出所有可用航线。"""
    return {
        "wci": dict(list(WCI_ROUTES.items())[:8]),
        "scfi": dict(list(SCFI_ROUTES.items())[:15]),
    }
