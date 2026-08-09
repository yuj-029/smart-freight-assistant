"""
到港提醒模块 - 基于 AIS 数据判断船舶是否接近目的港
触发条件：距目的港 ≤ 指定海里 或 距 ETA ≤ 指定天数
"""

import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 提醒阈值
ARRIVAL_THRESHOLD_NM = 200      # 距离目的港 ≤ 200 海里
ARRIVAL_THRESHOLD_DAYS = 2      # 距 ETA ≤ 2 天

# 主要港口坐标（纬度, 经度）
PORT_COORDS = {
    "USLAX": (33.73, -118.27), "USLGB": (33.75, -118.20),
    "USNYC": (40.64, -74.06),  "USSAV": (32.08, -81.09),
    "NLRTM": (51.90, 4.48),    "BEANR": (51.26, 4.39),
    "DEHAM": (53.54, 9.97),    "GBFXT": (51.95, 1.31),
    "CNSHA": (31.23, 121.47),  "CNNGB": (29.87, 121.55),
    "CNSZX": (22.54, 113.88),  "CNQDG": (36.07, 120.38),
    "CNYTN": (22.56, 114.30),  "SGSIN": (1.26, 103.76),
    "KRPUS": (35.10, 129.07),  "JPYOK": (35.44, 139.64),
    "HKHKG": (22.31, 114.17),  "TWKHH": (22.61, 120.28),
    "ITGOA": (44.41, 8.93),    "ESALG": (36.13, -5.43),
    "AUSYD": (-33.86, 151.21), "AUMEL": (-37.82, 144.93),
    "AUBNE": (-27.38, 153.12),
}


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算两点间海里距离（Haversine公式）。"""
    import math
    R = 3440.065  # 地球半径（海里）
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def check_arrival(
    vessel_name: str,
    latitude: float,
    longitude: float,
    destination_code: str,
    eta: Optional[str] = None,
    distance_threshold: float = ARRIVAL_THRESHOLD_NM,
    days_threshold: int = ARRIVAL_THRESHOLD_DAYS,
) -> Dict:
    """
    检查船舶是否接近目的港。

    Returns:
        {
            "vessel": str,
            "destination": str,
            "distance_nm": float or None,
            "distance_alert": bool,
            "eta_days_left": int or None,
            "eta_alert": bool,
            "should_alert": bool,
        }
    """
    result = {
        "vessel": vessel_name,
        "destination": destination_code,
        "distance_nm": None,
        "distance_alert": False,
        "eta_days_left": None,
        "eta_alert": False,
        "should_alert": False,
    }
    
    # 距离检测
    dest_coord = PORT_COORDS.get(destination_code.upper())
    if dest_coord and latitude and longitude:
        dist = haversine_nm(latitude, longitude, dest_coord[0], dest_coord[1])
        result["distance_nm"] = round(dist, 1)
        if dist <= distance_threshold:
            result["distance_alert"] = True
    
    # ETA 检测
    if eta:
        try:
            eta_date = datetime.date.fromisoformat(eta[:10])
            days = (eta_date - datetime.date.today()).days
            result["eta_days_left"] = days
            if 0 <= days <= days_threshold:
                result["eta_alert"] = True
        except (ValueError, TypeError):
            pass
    
    result["should_alert"] = result["distance_alert"] or result["eta_alert"]
    return result


def format_arrival_alert(check_result: Dict) -> Optional[str]:
    """生成到港提醒消息文本。"""
    if not check_result["should_alert"]:
        return None
    
    msg = f"🚢 **到港提醒**：{check_result['vessel']}\n"
    
    if check_result["distance_alert"]:
        msg += f"- 📍 距目的港约 {check_result['distance_nm']} 海里\n"
    if check_result["eta_alert"]:
        msg += f"- ⏰ 预计 {check_result['eta_days_left']} 天后到港"
        if check_result["eta_days_left"] == 0:
            msg += "（今天！）"
        elif check_result["eta_days_left"] == 1:
            msg += "（明天！）"
    return msg
