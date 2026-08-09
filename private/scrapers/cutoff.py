"""
截关预警模块 - 倒计时 + 单证到期提醒
Based on public port/shipping line schedules.
"""

import datetime
from typing import Dict, List, Optional, Tuple


# 常见单证类型及其典型有效期（天）
DOCUMENT_TYPES: Dict[str, Dict[str, object]] = {
    "FORM_M": {"name": "FORM M（尼日利亚进口许可）", "validity_days": 180, "renewal_days": 30},
    "ISF": {"name": "ISF 10+2（美国进口安全申报）", "validity_days": None, "filing_deadline": "装船前24小时"},
    "CTN": {"name": "CTN（西非货物跟踪单）", "validity_days": None, "filing_deadline": "装船前5个工作日"},
    "AMS": {"name": "AMS（美国舱单申报）", "validity_days": None, "filing_deadline": "装船前24小时"},
    "ENS": {"name": "ENS（欧盟入境摘要申报）", "validity_days": None, "filing_deadline": "装船前24小时"},
    "ACI": {"name": "ACI（埃及预申报）", "validity_days": None, "filing_deadline": "装船前48小时"},
    "BSC": {"name": "BSC（科特迪瓦货物跟踪单）", "validity_days": None, "filing_deadline": "装船前5个工作日"},
    "FUMIGATION": {"name": "熏蒸证书", "validity_days": 21, "note": "木质包装熏蒸后21天内有效"},
    "COO": {"name": "原产地证", "validity_days": 365, "note": "一般1年内有效"},
    "CERT_OF_INSURANCE": {"name": "保险单", "validity_days": None, "note": "覆盖全程运输"},
}

# 船公司 → (截关天数, 截单天数)
CARRIER_CUTOFF_WINDOWS = {
    "default": (5, 7),
    "COSCO": (4, 6),
    "MAERSK": (5, 7),
    "MSC": (5, 6),
    "CMA-CGM": (4, 7),
    "HAPAG-LLOYD": (5, 7),
    "ONE": (4, 6),
    "EVERGREEN": (5, 7),
    "HMM": (4, 6),
    "YANGMING": (5, 7),
    "ZIM": (5, 7),
    "WANHAI": (4, 6),
    "OOCL": (5, 7),
}


def calculate_cutoff_countdown(
    etd: datetime.date,
    cutoff_days_before: int = 5,
    doc_cutoff_days_before: int = 7
) -> Dict[str, object]:
    """
    计算截关/截单/ETD倒计时。

    Args:
        etd: 预计开船日期
        cutoff_days_before: 截关在ETD前N天（默认5天）
        doc_cutoff_days_before: 截单在ETD前N天（默认7天）

    Returns:
        含倒计时天数、紧急程度、各节点日期的字典
    """
    today = datetime.date.today()
    cutoff_date = etd - datetime.timedelta(days=cutoff_days_before)
    doc_cutoff_date = etd - datetime.timedelta(days=doc_cutoff_days_before)

    days_to_cutoff = (cutoff_date - today).days
    days_to_doc_cutoff = (doc_cutoff_date - today).days
    days_to_etd = (etd - today).days

    def urgency(days: int) -> str:
        if days < 0:
            return "🔴 已过期"
        elif days == 0:
            return "🔴 今天截止"
        elif days <= 1:
            return "🟡 紧迫（≤1天）"
        elif days <= 3:
            return "🟡 临近（≤3天）"
        elif days <= 7:
            return "🟢 正常（≤7天）"
        else:
            return "🟢 充裕（>7天）"

    return {
        "etd": str(etd),
        "cutoff_date": str(cutoff_date),
        "doc_cutoff_date": str(doc_cutoff_date),
        "days_to_cutoff": days_to_cutoff,
        "days_to_doc_cutoff": days_to_doc_cutoff,
        "days_to_etd": days_to_etd,
        "cutoff_urgency": urgency(days_to_cutoff),
        "doc_urgency": urgency(days_to_doc_cutoff),
    }


def check_document_expiry(
    doc_type: str,
    issue_date: Optional[datetime.date] = None,
    target_date: Optional[datetime.date] = None
) -> Dict[str, object]:
    """
    检查单证是否即将到期。

    Args:
        doc_type: 单证类型代码（见 DOCUMENT_TYPES）
        issue_date: 签发日期（有有效期的单证需要）
        target_date: 参考日期（默认今天）

    Returns:
        含到期信息、剩余天数、是否需续办的字典
    """
    doc_info = DOCUMENT_TYPES.get(doc_type.upper())
    if not doc_info:
        return {"error": f"未知单证类型: {doc_type}", "known_types": list(DOCUMENT_TYPES.keys())}

    validity = doc_info.get("validity_days")
    if validity is None:
        filing = doc_info.get("filing_deadline", "详见规则")
        return {
            "doc_type": doc_type.upper(),
            "doc_name": doc_info["name"],
            "type": "filing_deadline",
            "filing_deadline": filing,
            "expiry_urgent": False,
        }

    if issue_date is None:
        return {
            "doc_type": doc_type.upper(),
            "doc_name": doc_info["name"],
            "type": "validity_based",
            "validity_days": validity,
            "error": "需要提供签发日期才能计算到期日",
        }

    today = target_date or datetime.date.today()
    expiry_date = issue_date + datetime.timedelta(days=validity)
    days_left = (expiry_date - today).days

    return {
        "doc_type": doc_type.upper(),
        "doc_name": doc_info["name"],
        "type": "validity_based",
        "issue_date": str(issue_date),
        "expiry_date": str(expiry_date),
        "days_left": days_left,
        "expired": days_left < 0,
        "expiry_urgent": days_left <= 7,
        "needs_renewal": days_left <= 14 if validity > 30 else days_left <= 7,
        "note": doc_info.get("note", ""),
    }


def format_cutoff_report(
    vessel_name: str,
    voyage: str,
    etd: datetime.date,
    pol: str,
    pod: str,
    documents: Optional[List] = None,
    cutoff_days: int = 5,
    doc_cutoff_days: int = 7,
    carrier: Optional[str] = None
) -> str:
    """生成截关报告 Markdown 文本。carrier 用于查找船公司截关窗口配置。"""
    # 根据船公司查找截关/截单窗口
    if carrier:
        carrier_upper = carrier.strip().upper()
        if carrier_upper in CARRIER_CUTOFF_WINDOWS:
            cutoff_days, doc_cutoff_days = CARRIER_CUTOFF_WINDOWS[carrier_upper]
        else:
            cutoff_days, doc_cutoff_days = CARRIER_CUTOFF_WINDOWS["default"]

    cd = calculate_cutoff_countdown(etd, cutoff_days, doc_cutoff_days)

    report = f"""## 🚢 {vessel_name} / {voyage}

| 项目 | 日期 | 倒计时 | 状态 |
|------|------|--------|------|
| ETD（预计开船） | {etd} | {cd['days_to_etd']} 天 | — |
| 截关（VGM/放行） | {cd['cutoff_date']} | {cd['days_to_cutoff']} 天 | {cd['cutoff_urgency']} |
| 截单（舱单/AMS） | {cd['doc_cutoff_date']} | {cd['days_to_doc_cutoff']} 天 | {cd['doc_urgency']} |

📍 {pol} → {pod}
"""

    if documents:
        report += "\n### 📋 单证检查\n"
        for doc in documents:
            # 兼容旧格式（字符串）和新格式（Dict 含 issue_date）
            if isinstance(doc, str):
                result = check_document_expiry(doc.upper())
            elif isinstance(doc, dict):
                doc_type = doc.get("type", "").upper()
                issue_str = doc.get("issue_date")
                issue_date = None
                if issue_str:
                    try:
                        issue_date = datetime.date.fromisoformat(issue_str)
                    except (ValueError, TypeError):
                        pass
                result = check_document_expiry(doc_type, issue_date=issue_date)
            else:
                continue

            if result.get("type") == "filing_deadline":
                report += f"- **{result['doc_name']}**：申报截止 {result['filing_deadline']}\n"
            elif result.get("expired"):
                report += f"- 🔴 **{result['doc_name']}**：已过期 {abs(result['days_left'])} 天，需立即续办\n"
            elif result.get("expiry_urgent"):
                report += f"- 🟡 **{result['doc_name']}**：距到期仅 {result['days_left']} 天\n"
            elif result.get("needs_renewal"):
                report += f"- 🟢 **{result['doc_name']}**：剩余 {result['days_left']} 天，建议续办\n"
            else:
                report += f"- ✅ **{result['doc_name']}**：剩余 {result.get('days_left', '—')} 天\n"

    return report
