"""
智能货代助手 — 四通道通知调度 / Notification Dispatcher

本文件包含实际的推送逻辑，属于私有层，不进入公开 GitHub 仓库。
Skill 主体（SKILL.md）仅描述推送通道的存在和交互流程，
具体实现（SMTP 授权码拼接、Webhook 签名、重试策略）全部在此。

支持通道 / Channels:
  - wecom:    企业微信机器人
  - dingtalk: 钉钉机器人
  - email:    QQ邮箱 SMTP
  - bark:     Bark (iOS)
"""

import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

# 配置文件路径
CONFIG_DIR = Path(__file__).parent
ENV_FILE = CONFIG_DIR / ".env"


def load_env():
    """加载 .env 环境变量"""
    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f".env not found. Copy .env.template to .env and fill in credentials."
        )
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


def send_wecom(message: str, title: Optional[str] = None) -> bool:
    """企业微信机器人推送"""
    webhook = os.getenv("WECOM_WEBHOOK_URL")
    if not webhook:
        return False
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"## {title or '智能货代助手'}\n{message}"
        }
    }
    resp = requests.post(webhook, json=payload, timeout=10)
    return resp.status_code == 200


def send_dingtalk(message: str, title: Optional[str] = None) -> bool:
    """钉钉机器人推送"""
    webhook = os.getenv("DINGTALK_WEBHOOK_URL")
    if not webhook:
        return False
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title or "智能货代助手",
            "text": f"### {title or '智能货代助手'}\n{message}"
        }
    }
    resp = requests.post(webhook, json=payload, timeout=10)
    return resp.status_code == 200


def send_email(message: str, title: Optional[str] = None) -> bool:
    """QQ邮箱 SMTP 推送"""
    sender = os.getenv("QQ_EMAIL_SENDER")
    auth_code = os.getenv("QQ_EMAIL_SMTP_AUTH_CODE")
    receiver = os.getenv("QQ_EMAIL_RECEIVER")
    if not all([sender, auth_code, receiver]):
        return False

    msg = MIMEText(message, "plain", "utf-8")
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = title or "智能货代助手通知"

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=10)
        server.login(sender, auth_code)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        return True
    except Exception:
        return False


def send_bark(message: str, title: Optional[str] = None) -> bool:
    """Bark (iOS) 推送"""
    bark_key = os.getenv("BARK_KEY")
    if not bark_key:
        return False
    url = f"https://api.day.app/{bark_key}/{title or '智能货代助手'}/{message}"
    resp = requests.get(url, timeout=10)
    return resp.status_code == 200


def notify(message: str, title: Optional[str] = None, channel: str = "wecom") -> dict:
    """
    统一通知入口。根据配置的通道发送通知。
    返回 {"success": bool, "channel": str}
    """
    load_env()

    dispatchers = {
        "wecom": send_wecom,
        "dingtalk": send_dingtalk,
        "email": send_email,
        "bark": send_bark,
    }

    send_fn = dispatchers.get(channel)
    if not send_fn:
        return {"success": False, "channel": channel, "error": "Unknown channel"}

    success = send_fn(message, title)
    return {"success": success, "channel": channel}


if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "测试消息"
    ch = sys.argv[2] if len(sys.argv) > 2 else "wecom"
    result = notify(msg, title="智能货代助手", channel=ch)
    print(json.dumps(result, ensure_ascii=False))
