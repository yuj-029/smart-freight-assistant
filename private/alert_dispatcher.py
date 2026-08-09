"""
统一告警调度器 - 所有模块的推送入口

支持告警类型：
- tracking_delay: 船期延误
- tracking_signal_loss: AIS 信号丢失
- tracking_arrival: 到港提醒
- cutoff_expiring: 截关临近
- cutoff_doc_expiring: 单证到期
- price_alert: 运价波动
- usage_warning: 免费额度预警
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).parent / "data"
ALERT_LOG = DATA_DIR / "alert_log.json"

ALERT_SEVERITY = {
    "tracking_delay": "🟡",
    "tracking_signal_loss": "🔴",
    "tracking_arrival": "🔵",
    "cutoff_expiring": "🔴",
    "cutoff_doc_expiring": "🟡",
    "price_alert": "🟠",
    "usage_warning": "🟡",
}


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_log() -> List[Dict]:
    _ensure_data_dir()
    if not ALERT_LOG.exists():
        return []
    with open(ALERT_LOG, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_log(log: List[Dict]):
    _ensure_data_dir()
    with open(ALERT_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def dispatch(
    alert_type: str,
    title: str,
    message: str,
    channel: str = "wecom",
    dedup_key: Optional[str] = None,
) -> Dict:
    """
    统一告警入口。

    Args:
        alert_type: 告警类型（见 ALERT_SEVERITY）
        title: 告警标题
        message: 告警正文
        channel: 推送通道（wecom/dingtalk/email/bark）
        dedup_key: 去重键（同键24h内不重复推送）

    Returns:
        {"dispatched": bool, "channel": str, "dedup_skipped": bool}
    """
    log = _load_log()
    
    # 去重检查
    if dedup_key:
        today = str(date.today())
        for entry in log:
            if entry.get("dedup_key") == dedup_key and entry.get("date") == today:
                return {"dispatched": False, "channel": channel, "dedup_skipped": True, "reason": "24h内已推送"}

    severity = ALERT_SEVERITY.get(alert_type, "")
    full_title = f"{severity} {title}" if severity else title

    # 记录日志
    log.append({
        "type": alert_type,
        "title": title,
        "channel": channel,
        "date": str(date.today()),
        "time": str(datetime.now()),
        "dedup_key": dedup_key,
    })
    _save_log(log)

    # 调用 notify 推送
    try:
        from notify import notify
        result = notify(message=message, title=full_title, channel=channel)
        return {"dispatched": result.get("success", False), "channel": channel, "dedup_skipped": False}
    except ImportError:
        return {"dispatched": False, "channel": channel, "dedup_skipped": False, "error": "notify模块不可用"}
    except Exception as e:
        return {"dispatched": False, "channel": channel, "dedup_skipped": False, "error": str(e)}


def get_alert_history(days: int = 7) -> List[Dict]:
    """获取最近 N 天告警历史。"""
    log = _load_log()
    cutoff = str(date.today())
    try:
        cutoff_date = date.today() - __import__("datetime").timedelta(days=days)
        cutoff = str(cutoff_date)
    except:
        pass
    return [e for e in log if e.get("date", "") >= cutoff]
