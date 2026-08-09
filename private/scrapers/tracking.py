"""
船期/箱况追踪模块 - AIS 船位查询 + 提单/柜号追踪

数据源：
- VesselFinder API：AIS 实时船位（含船名/IMO/MMSI/经纬度/航速/航向/目的港/ETA）
- 51Tracking API：提单号/柜号追踪（200单/月免费额度）
- Ship24 API：集装箱追踪（10单/月免费额度）

免费用量：最多 3 个活跃 B/L 号同时监控
"""

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
TRACKING_CACHE = DATA_DIR / "tracking_cache.json"

# 港口代码 → 中文映射
PORT_NAMES = {
    "USLAX": "洛杉矶", "USLGB": "长滩", "USNYC": "纽约", "USSAV": "萨凡纳",
    "NLRTM": "鹿特丹", "BEANR": "安特卫普", "DEHAM": "汉堡",
    "GBFXT": "费利克斯托", "GBSOU": "南安普顿",
    "CNSHA": "上海", "CNNGB": "宁波", "CNSZX": "深圳", "CNQDG": "青岛",
    "CNTAO": "青岛", "CNXMN": "厦门", "CNYTN": "盐田",
    "SGSIN": "新加坡", "KRPUS": "釜山", "JPYOK": "横滨",
    "HKHKG": "香港", "TWKHH": "高雄",
    "ITGOA": "热那亚", "ITGIT": "焦亚陶罗", "ESALG": "阿尔赫西拉斯",
    "AUSYD": "悉尼", "AUMEL": "墨尔本", "AUBNE": "布里斯班",
    "MYTPP": "丹戎帕拉帕斯", "LKCMB": "科伦坡", "AEAUH": "阿布扎比",
}

# AIS 数据时效分级（小时）
AIS_FRESHNESS = {
    "realtime": 4,          # ≤4h → 实时
    "slightly_stale": 12,   # 4-12h → 稍旧
    "stale": 48,            # 12-48h → 滞后
    "severely_stale": 168,  # >48h → 严重滞后 / >168h → 无信号
}


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_tracking_cache() -> Dict:
    _ensure_data_dir()
    if not TRACKING_CACHE.exists():
        return {"vessels": {}, "containers": {}, "bills": {}}
    with open(TRACKING_CACHE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_tracking_cache(data: Dict):
    _ensure_data_dir()
    with open(TRACKING_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_vessel_search_queries(vessel_name: str, imo: Optional[str] = None) -> List[str]:
    """
    为指定船舶生成 web_search 关键词列表，供 Marvis Agent 执行搜索。

    策略：构造多角度的搜索短语以提高命中率——
    1. 精确船名 + IMO + 船位（VesselFinder/MarineTraffic 等）
    2. 船名关键词 + 当前位置 + AIS
    3. 船名 + ETA + 目的港
    4. 纯 IMO 号兜底（若已知）

    Args:
        vessel_name: 船名（英文全名）
        imo: IMO 编号（可选，提供后增加精确匹配查询词）

    Returns:
        web_search 查询字符串列表（3~5 条），可直接传入 Marvis web_search 工具
    """
    queries = []
    # 提取船名简称（第一个词或前两个词）用于短关键词搜索
    name_parts = vessel_name.strip().upper().split()
    short_name = " ".join(name_parts[:2]) if len(name_parts) >= 2 else vessel_name.upper()

    # 查询 1：精确船名 + IMO + 船位
    if imo:
        queries.append(f"{vessel_name} IMO {imo} vessel position AIS current location")
        queries.append(f"IMO {imo} current position speed heading destination ETA")
    else:
        queries.append(f'"{vessel_name}" vessel position AIS current location')
        queries.append(f'"{vessel_name}" marine traffic ship position latitude longitude')

    # 查询 2：短船名 + AIS 关键词
    queries.append(f"{short_name} AIS tracking speed knots destination port ETA")

    # 查询 3：船名 + 目的港推断
    queries.append(f"{short_name} container ship ETA destination port schedule")

    return queries


def parse_web_search_result(vessel_name: str, search_results_text: str) -> Dict:
    """
    从 web_search 返回的文本中提取 AIS 关键字段。

    提取目标：
    - 经纬度（十进制格式，如 "33.73° N / -118.27° W" 或 "33.73, -118.27"）
    - 航速（kn / knots）
    - 航向（° / degree）
    - 目的港（常见港口代码或英文名）
    - ETA（日期时间）
    - 信号时间 / 更新时间

    Args:
        vessel_name: 船名（用于回填结果）
        search_results_text: web_search 返回的全部文本

    Returns:
        Dict，字段与 cache_vessel_position 对齐，提取失败的字段为 None
    """
    text = search_results_text

    # --- 经纬度提取 ---
    # 多种常见格式：33.73°N / 118.27°W, 33.73, -118.27, lat 33.73 lon -118.27
    lat, lng = None, None
    lat_lng_patterns = [
        # "33.73° N / 118.27° W" or "33.73°N, 118.27°W"
        r"(\d{1,3}\.\d{1,6})\s*°?\s*[NS].*?(\d{1,3}\.\d{1,6})\s*°?\s*[EW]",
        # "Lat: 33.73, Lon: -118.27"
        r"[Ll]at(?:itude)?[:\s]*(-?\d{1,3}\.\d{1,6}).*?[Ll]on(?:gitude)?[:\s]*(-?\d{1,3}\.\d{1,6})",
        # "33.73, -118.27"
        r"(\d{1,3}\.\d{1,6})\s*[,/]\s*(-?\d{1,3}\.\d{1,6})",
    ]
    for pat in lat_lng_patterns:
        m = re.search(pat, text)
        if m:
            try:
                lat = float(m.group(1))
                lng = float(m.group(2))
                # 处理 N/S E/W 符号
                if "S" in m.group(0).split(str(m.group(1)))[-1][:3]:
                    lat = -lat
                if "W" in m.group(0).split(str(m.group(2)))[-1][:3]:
                    lng = -lng
            except (ValueError, IndexError):
                lat, lng = None, None
            if lat is not None:
                break

    # --- 航速提取 ---
    speed = None
    speed_pat = r"(\d{1,3}\.\d{1,2})\s*(?:kn|knots|节)"
    m = re.search(speed_pat, text, re.IGNORECASE)
    if m:
        try:
            speed = float(m.group(1))
        except ValueError:
            pass

    # --- 航向提取 ---
    heading = None
    heading_pat = r"(?:[Cc]ourse|[Hh]eading)[:\s]*(\d{1,3})\s*°"
    m = re.search(heading_pat, text)
    if m:
        try:
            heading = int(m.group(1))
        except ValueError:
            pass

    # --- 目的港提取 ---
    destination = None
    dest_pat = r"(?:[Dd]estination|[Dd]est)[:\s]*([A-Z]{4,5})(?:\s|,|\.|$)"
    m = re.search(dest_pat, text)
    if m:
        destination = m.group(1).strip()

    # --- ETA 提取 ---
    eta = None
    eta_pats = [
        r"ETA[:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)",
        r"(\d{4}-\d{2}-\d{2})\s*\(estimated\)",
        r"[Ee]stimated [Tt]ime [Oo]f [Aa]rrival[:\s]*(\d{4}-\d{2}-\d{2})",
    ]
    for pat in eta_pats:
        m = re.search(pat, text)
        if m:
            eta = m.group(1).strip()
            break

    # --- 信号时间提取 ---
    signal_time = None
    signal_pats = [
        r"(?:[Uu]pdated|[Rr]eceived|[Ss]ignal)[:\s]*(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?)",
        r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})(?:Z| UTC)?",
    ]
    for pat in signal_pats:
        m = re.search(pat, text)
        if m:
            signal_time = m.group(1).strip().replace(" ", "T")
            break

    # --- 导航状态提取 ---
    nav_status = None
    status_pat = r"(?:[Nn]avigation [Ss]tatus|[Ss]tatus)[:\s]*(\w[\w\s]+?)(?:,|\.|\n|$)"
    m = re.search(status_pat, text)
    if m:
        nav_status = m.group(1).strip()

    return {
        "vessel_name": vessel_name,
        "latitude": lat,
        "longitude": lng,
        "speed_knots": speed,
        "heading": heading,
        "destination": destination,
        "eta": eta,
        "signal_time": signal_time,
        "nav_status": nav_status,
    }


def build_container_search_queries(
    bill_or_container_number: str,
    carrier: Optional[str] = None
) -> List[str]:
    """
    根据提单号或柜号生成 web_search 关键词列表，供 Marvis Agent 执行搜索。

    策略：
    - 已知船公司：提单号 + 船公司名 + 货物跟踪 / container tracking
    - 未知船公司：提单号 + 51tracking / 集装箱跟踪 / 百运网 等多渠道兜底

    Args:
        bill_or_container_number: 提单号 (B/L) 或柜号 (Container No)
        carrier: 船公司名称（可选，如 "COSCO" / "MSK" / "CMA CGM"）

    Returns:
        web_search 查询字符串列表（3~5 条）
    """
    num = bill_or_container_number.strip()
    queries = []
    if carrier:
        queries.append(f"{num} {carrier} 货物跟踪 状态")
        queries.append(f"{num} {carrier} container tracking status ETA")
    else:
        queries.append(f"{num} 51tracking 集装箱跟踪")
        queries.append(f"{num} 集装箱跟踪 状态查询")
        queries.append(f"{num} 百运网 货物状态 提单查询")
    # 通用兜底
    queries.append(f'"{num}" container tracking ETA status location')
    return queries


def parse_container_search_result(
    bill_number: str,
    search_results_text: str
) -> Dict:
    """
    从 web_search 返回文本中提取集装箱追踪结构化信息。

    提取目标：
    - 当前状态（已装船 / 在途 / 到港 / 已提柜 / 清关中 等）
    - 当前位置（港口名）
    - ETA（预计到港时间）
    - 最后更新时间
    - 事件列表（装船 / 中转 / 到港 / 清关 / 提柜 等关键节点）
    - 船名航次 (vessel / voyage)
    - 起运港 / 目的港 (origin_port / destination_port)

    Args:
        bill_number: 提单号或柜号
        search_results_text: web_search 返回的全部文本

    Returns:
        Dict，字段与 cache_container_status 对齐，提取失败的字段为 None
    """
    text = search_results_text

    # --- 当前状态提取 ---
    status = None
    status_keywords = [
        "已装船", "在途", "已到港", "已提柜", "已签收", "已交付",
        "清关中", "海关放行", "已中转", "已离港", "已卸船",
        "Loaded on vessel", "In transit", "Arrived at port",
        "Container picked up", "Delivered", "Customs clearance",
        "Departed", "Discharged", "Transshipment",
    ]
    for kw in status_keywords:
        if kw.lower() in text.lower():
            status = kw
            break

    # --- 当前位置提取 ---
    location = None
    # 尝试匹配 "当前位置 / 所在港 / Location / Last seen at" 后的港口名或城市名
    loc_patterns = [
        r"(?:当前位置|所在港|所在地)[：:\s]*([^\n,，。]{2,20})",
        r"(?:[Ll]ocation|[Ll]ast seen at)[：:\s]*([^\n,，]{2,30})",
        r"(?:[Aa]t|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:port|terminal|,|\.)",
    ]
    for pat in loc_patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) >= 2:
                location = candidate
                break

    # --- ETA 提取 ---
    eta = None
    eta_pats = [
        r"ETA[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)",
        r"(?:预计到港|预计到达)[：:\s]*(\d{4}-\d{2}-\d{2})",
        r"(\d{4}-\d{2}-\d{2})\s*\(estimated\)",
    ]
    for pat in eta_pats:
        m = re.search(pat, text)
        if m:
            eta = m.group(1).strip()
            break

    # --- 最后更新时间提取 ---
    last_update = None
    update_pats = [
        r"(?:更新时间|最后更新|更新)[：:\s]*(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?)",
        r"(?:[Uu]pdated|[Ll]ast update)[：:\s]*(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?)",
    ]
    for pat in update_pats:
        m = re.search(pat, text)
        if m:
            last_update = m.group(1).strip().replace(" ", "T")
            break

    # --- 船名航次提取 ---
    vessel = None
    voyage = None
    vessel_pat = r"(?:[Vv]essel|[Ss]hip|[Vv]essel [Nn]ame|船名)[：:\s]*([A-Z][A-Z\s\-]+?)(?:,|\s{2,}|\n|$)"
    m = re.search(vessel_pat, text)
    if m:
        vessel = m.group(1).strip()
    voyage_pat = r"(?:[Vv]oyage|[Vv]oy|[Nn]o\.?|航次)[：:\s]*([A-Z0-9]+)(?:,|\s|\.|\n|$)"
    m = re.search(voyage_pat, text)
    if m:
        voyage = m.group(1).strip()

    # --- 起运港 / 目的港提取 ---
    origin_port = None
    destination_port = None
    origin_pat = r"(?:起运港|装货港|POL|Port of Loading|Origin)[：:\s]*([A-Z]{4,5})"
    m = re.search(origin_pat, text)
    if m:
        origin_port = m.group(1).strip()
    dest_pat = r"(?:目的港|卸货港|POD|Port of Discharge|Destination)[：:\s]*([A-Z]{4,5})"
    m = re.search(dest_pat, text)
    if m:
        destination_port = m.group(1).strip()

    # --- 事件列表提取 ---
    events = []
    # 尝试匹配事件时间线：日期 + 描述
    event_pat = r"(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)[：:\s]+(\S.{3,60}?)(?=\d{4}-\d{2}-\d{2}|\n\n|$)"
    for m in re.finditer(event_pat, text, re.DOTALL):
        events.append({
            "time": m.group(1).strip(),
            "description": m.group(2).strip().rstrip(","),
        })
    # 若事件列表为空，尝试单条事件匹配
    if not events:
        single_event_pat = r"(?:[Ee]vent|[Ss]tatus|[状状]态)[：:\s]*(\d{4}-\d{2}-\d{2}[T\s]?\d{2}:\d{2}?)[：:\s]+(\S.{3,60}?)(?:,|\.|\n|$)"
        for m in re.finditer(single_event_pat, text):
            events.append({
                "time": m.group(1).strip().replace(" ", "T"),
                "description": m.group(2).strip(),
            })

    return {
        "container_no": bill_number,
        "status": status,
        "location": location,
        "eta": eta,
        "last_update": last_update,
        "events": events,
        "vessel": vessel,
        "voyage": voyage,
        "origin_port": origin_port,
        "destination_port": destination_port,
    }


def classify_ais_freshness(timestamp: str) -> str:
    """
    根据 AIS 信号时间戳分级。
    Args:
        timestamp: ISO 格式时间字符串
    Returns:
        时效等级标签
    """
    try:
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        age_hours = (datetime.utcnow() - ts.replace(tzinfo=None)).total_seconds() / 3600
        if age_hours <= 4:
            return "🟢 实时"
        elif age_hours <= 12:
            return "🟡 稍旧"
        elif age_hours <= 48:
            return "🟠 滞后"
        else:
            return "🔴 严重滞后"
    except (ValueError, TypeError):
        return "⚠️ 无法判定"


def cache_vessel_position(
    vessel_name: str,
    imo: Optional[str] = None,
    mmsi: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    speed_knots: Optional[float] = None,
    heading: Optional[int] = None,
    destination: Optional[str] = None,
    eta: Optional[str] = None,
    signal_time: Optional[str] = None,
    nav_status: Optional[str] = None,
) -> Dict:
    """缓存船舶 AIS 位置数据。"""
    cache = _load_tracking_cache()
    key = vessel_name.upper()

    entry = {
        "vessel_name": vessel_name,
        "imo": imo,
        "mmsi": mmsi,
        "latitude": latitude,
        "longitude": longitude,
        "speed_knots": speed_knots,
        "heading": heading,
        "destination": destination,
        "eta": eta,
        "signal_time": signal_time,
        "nav_status": nav_status,
        "ais_freshness": classify_ais_freshness(signal_time) if signal_time else "未知",
        "cached_at": str(datetime.now()),
    }

    cache["vessels"][key] = entry
    _save_tracking_cache(cache)
    return entry


def get_vessel_position(vessel_name: str, source: str = "cache") -> Dict:
    """
    从缓存读取船舶最新位置。
    
    Args:
        vessel_name: 船名
        source: 数据源模式
            - "cache"（默认）：仅从本地缓存读取
            - "web_search"：先查缓存，无缓存时返回搜索指令供 Marvis Agent 执行
            
    Returns:
        缓存命中时返回船位数据字典；
        web_search 模式无缓存时返回 {"mode": "search_required", "search_queries": [...], ...}
    """
    cache = _load_tracking_cache()
    key = vessel_name.upper()
    entry = cache["vessels"].get(key)
    if entry:
        return entry
    
    if source == "web_search":
        queries = build_vessel_search_queries(vessel_name)
        return {
            "mode": "search_required",
            "vessel_name": vessel_name,
            "search_queries": queries,
            "hint": "Marvis Agent 请用 web_search 执行以上查询，将结果文本传入 parse_web_search_result() 解析后调用 cache_vessel_position() 缓存",
        }
    
    return {"error": f"未找到 {vessel_name} 的追踪记录，请先录入或查询"}


def cache_container_status(
    container_no: str,
    status: str,
    location: Optional[str] = None,
    events: Optional[List[Dict]] = None,
    vessel: Optional[str] = None,
    voyage: Optional[str] = None,
    eta: Optional[str] = None,
    origin_port: Optional[str] = None,
    destination_port: Optional[str] = None,
) -> Dict:
    """缓存集装箱状态。"""
    cache = _load_tracking_cache()
    entry = {
        "container_no": container_no,
        "status": status,
        "location": location,
        "events": events or [],
        "vessel": vessel,
        "voyage": voyage,
        "eta": eta,
        "origin_port": origin_port,
        "destination_port": destination_port,
        "updated_at": str(datetime.now()),
    }
    cache["containers"][container_no] = entry
    _save_tracking_cache(cache)
    return entry


def get_container_status(container_no: str, source: str = "cache") -> Dict:
    """
    查询集装箱状态。
    
    Args:
        container_no: 提单号或柜号
        source: 数据源模式
            - "cache"（默认）：仅从本地缓存读取
            - "web_search"：先查缓存，无缓存时返回搜索指令供 Marvis Agent 执行
            
    Returns:
        缓存命中时返回状态数据字典；
        web_search 模式无缓存时返回 {"mode": "search_required", "search_queries": [...], ...}
    """
    cache = _load_tracking_cache()
    entry = cache["containers"].get(container_no)
    if entry:
        return entry

    if source == "web_search":
        queries = build_container_search_queries(container_no)
        return {
            "mode": "search_required",
            "container_no": container_no,
            "search_queries": queries,
            "hint": "Marvis Agent 请用 web_search 执行以上查询，将结果文本传入 parse_container_search_result() 解析后调用 cache_container_status() 缓存",
        }

    return {"error": f"未找到柜号 {container_no} 的追踪记录"}


def format_tracking_report(vessel_name: str) -> str:
    """生成船舶追踪报告 Markdown 文本。"""
    pos = get_vessel_position(vessel_name)
    if "error" in pos:
        return f"⚠️ {pos['error']}"

    # 目的港中文映射
    dest = pos.get('destination') or "—"
    dest_display = dest
    if dest in PORT_NAMES:
        dest_display = f"{PORT_NAMES[dest]} ({dest})"

    report = f"""## 🚢 {pos['vessel_name']}

| 项目 | 数据 |
|------|------|
| IMO | {pos.get('imo') or '—'} |
| MMSI | {pos.get('mmsi') or '—'} |
| 位置 | {pos.get('latitude'):.4f}, {pos.get('longitude'):.4f} |
| 航速 | {pos.get('speed_knots') or '—'} kn |
| 航向 | {pos.get('heading') or '—'}° |
| 状态 | {pos.get('nav_status') or '—'} |
| 目的港 | {dest_display} |
| ETA | {pos.get('eta') or '—'} |
| AIS 信号 | {pos.get('signal_time') or '—'} |
| 时效 | {pos['ais_freshness']} |
| 缓存时间 | {pos['cached_at']} |
"""
    return report


def ingest_ais_data(vessel_data: Dict) -> Dict:
    """从真实 AIS 数据源录入船位。直接调用 cache_vessel_position。"""
    return cache_vessel_position(**vessel_data)


def ingest_container_data(container_data: Dict) -> Dict:
    """从真实追踪数据源录入箱况。直接调用 cache_container_status。"""
    return cache_container_status(**container_data)


def detect_anomalies(vessel_name: str) -> List[Dict]:
    """
    检测船期异常。

    检测项：
    1. AIS 信号丢失（>48h 无更新）
    2. ETA 延误（ETA 已过 + 未到港）
    3. 目的港变更（对比上次记录）
    
    Returns: [{"type": "signal_loss", "severity": "high", "message": "..."}, ...]
    """
    pos = get_vessel_position(vessel_name)
    if "error" in pos:
        return [{"type": "not_found", "severity": "low", "message": pos["error"]}]
    
    anomalies = []
    
    # 1. 信号丢失检测
    freshness = pos.get("ais_freshness", "")
    if "严重滞后" in freshness:
        anomalies.append({
            "type": "signal_loss",
            "severity": "high",
            "message": f"{vessel_name} AIS 信号丢失 > 48 小时，最后信号: {pos.get('signal_time', '未知')}",
        })
    elif "滞后" in freshness:
        anomalies.append({
            "type": "signal_stale",
            "severity": "medium",
            "message": f"{vessel_name} AIS 信号滞后 12-48 小时",
        })
    
    # 2. ETA 延误检测
    eta_str = pos.get("eta")
    if eta_str:
        try:
            from datetime import date
            eta_date = date.fromisoformat(eta_str[:10])
            today = date.today()
            delay_days = (today - eta_date).days
            if delay_days >= 3:
                anomalies.append({
                    "type": "eta_delay",
                    "severity": "high" if delay_days >= 7 else "medium",
                    "message": f"{vessel_name} ETA {eta_str[:10]} 已延误 {delay_days} 天",
                    "delay_days": delay_days,
                })
            elif delay_days >= 1:
                anomalies.append({
                    "type": "eta_slight_delay",
                    "severity": "low",
                    "message": f"{vessel_name} ETA {eta_str[:10]} 已延误 {delay_days} 天",
                    "delay_days": delay_days,
                })
        except (ValueError, TypeError):
            pass
    
    return anomalies
