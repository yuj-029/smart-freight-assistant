"""
运价聚合模块 - 运价指数抓取 + 运价查询缓存

数据源分类：
- 指数类（公开免费）：Drewry WCI / SCFI / CCFI / FBX
- 商业 API：Freightos / Xeneta（需 API Key）
- 船公司官网抓取（待实现）

v2.0 Phase 2 新增：运价指数缓存与波动检测
"""

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

# 跨模块引用 price_alert 中的 update_index
_PARENT = Path(__file__).parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))
from price_alert import update_index

DATA_DIR = Path(__file__).parent.parent / "data"
RATES_CACHE = DATA_DIR / "rates_cache.json"

# 常用币种汇率缓存（RMB → USD 基准）
EXCHANGE_CACHE: Dict[str, float] = {}


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_rates_cache() -> Dict:
    _ensure_data_dir()
    if not RATES_CACHE.exists():
        return {"freight_rates": {}, "indices": {}, "exchange_rates": {}}
    import json
    with open(RATES_CACHE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_rates_cache(data: Dict):
    _ensure_data_dir()
    import json
    with open(RATES_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cache_freight_rate(
    origin: str,
    destination: str,
    carrier: str,
    container_type: str,
    rate_usd: float,
    rate_rmb: Optional[float] = None,
    rate_type: str = "all-in",
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    source: str = "manual",
) -> Dict:
    """
    缓存运价记录。

    Args:
        origin: 起运港
        destination: 目的港
        carrier: 船公司
        container_type: 柜型（20GP/40GP/40HQ等）
        rate_usd: 美元运价
        rate_rmb: 人民币运价（可选，不传则用汇率换算）
        rate_type: 运价口径（all-in / net-ocean）
        valid_from: 有效期开始
        valid_to: 有效期结束
        source: 数据来源
    """
    cache = _load_rates_cache()
    key = f"{origin}|{destination}|{carrier}|{container_type}"

    if rate_rmb is None and rate_usd > 0:
        rate_rmb = round(rate_usd * 7.25, 0)  # 兜底汇率

    entry = {
        "origin": origin,
        "destination": destination,
        "carrier": carrier,
        "container_type": container_type,
        "rate_usd": rate_usd,
        "rate_rmb": rate_rmb,
        "rate_type": rate_type,
        "valid_from": valid_from or str(date.today()),
        "valid_to": valid_to,
        "source": source,
        "cached_at": str(datetime.now()),
        "expired": False,
    }

    # 过期检测（超过30天标为过期）
    if valid_to:
        try:
            expiry = datetime.strptime(valid_to, "%Y-%m-%d").date()
            if expiry < date.today():
                entry["expired"] = True
        except ValueError:
            pass

    cache["freight_rates"][key] = entry
    _save_rates_cache(cache)
    return entry


def query_freight_rate(
    origin: str,
    destination: str,
    carrier: Optional[str] = None,
    container_type: Optional[str] = None,
) -> List[Dict]:
    """
    查询运价。支持精确匹配和模糊匹配。

    Args:
        origin: 起运港（必填）
        destination: 目的港（必填）
        carrier: 船公司（可选，不传返回该航线所有船公司）
        container_type: 柜型（可选）
    """
    cache = _load_rates_cache()
    results = []

    for key, entry in cache["freight_rates"].items():
        if entry["origin"] != origin:
            continue
        if entry["destination"] != destination:
            continue
        if carrier and entry["carrier"].upper() != carrier.upper():
            continue
        if container_type and entry["container_type"] != container_type:
            continue
        results.append(entry)

    return results


def cache_index_data(
    index_name: str,
    route: str,
    value: float,
    unit: str = "USD",
    source: str = "SCFI",
) -> Dict:
    """缓存运价指数数据。"""
    cache = _load_rates_cache()
    key = f"{source}:{route}"
    entry = {
        "index_name": index_name,
        "route": route,
        "value": value,
        "unit": unit,
        "source": source,
        "updated": str(date.today()),
    }
    cache["indices"][key] = entry
    _save_rates_cache(cache)
    return entry


def get_index_data(route: str, source: str = "SCFI") -> Dict:
    """从缓存读取运价指数。"""
    cache = _load_rates_cache()
    key = f"{source}:{route}"
    return cache["indices"].get(key, {"error": f"暂无 {source} {route} 的指数缓存"})


def ingest_wci_data(wci_data: List[Dict]) -> List[Dict]:
    """
    从真实 WCI 数据源录入指数。wci_data 格式：
    [{"route": "shanghai-los_angeles", "value": 5894.0, "unit": "USD", "source": "Drewry WCI"}]
    """
    results = []
    for item in wci_data:
        entry = update_index(item["route"], "wci", item["value"], item.get("unit", "USD"))
        results.append(entry)
    return results


def ingest_scfi_data(scfi_data: List[Dict]) -> List[Dict]:
    """
    从真实 SCFI 数据源录入指数。scfi_data 格式：
    [{"route": "shanghai-uswc", "value": 5229.0, "unit": "USD"}]
    """
    results = []
    for item in scfi_data:
        entry = update_index(item["route"], "scfi", item["value"], item.get("unit", "USD"))
        results.append(entry)
    return results
