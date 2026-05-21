import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_telegram_alert(chat_id: str, app_id: str, result: dict):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("[Telegram] Bot token not configured in .env. Skipping.")
        return
    
    # Rich emoji mappings for all security states
    emoji = {
        "SAFE": "🟢",
        "LOW RISK": "🔵",
        "WARNING": "🟡",
        "SUSPICIOUS": "⚠️",
        "HIGH RISK": "🟠",
        "HIGH": "🔴",
        "VULNERABLE": "💀",
        "INACTIVE": "⚪",
        "ERROR": "❌",
    }.get(result.get("severity", "HIGH"), "⚠️")
    
    severity = result.get("severity", "Unknown")
    description = result.get("description", "Suspicious transaction detected.")
    
    # Determine the appropriate block explorer link
    target_str = str(app_id).strip()
    if len(target_str) == 58:
        explorer_url = f"https://allo.info/account/{target_str}"
        target_label = "Account Address"
    else:
        explorer_url = f"https://allo.info/app/{target_str}"
        target_label = "Application ID"
    
    # HTML formatting is extremely robust compared to picky markdown escaping
    text = (
        f"{emoji} <b>AlgoShield Live Security Alert</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Target type:</b> {target_label}\n"
        f"<b>Target:</b> <code>{target_str}</code>\n"
        f"<b>Risk Status:</b> <b>{severity}</b>\n\n"
        f"<b>Details:</b>\n{description}\n\n"
        f"🔍 <a href='{explorer_url}'>View on Block Explorer</a>"
    )
    
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=8
        )
        res.raise_for_status()
        logger.info(f"[Telegram] Alert sent successfully to chat_id {chat_id}")
    except Exception as e:
        logger.error(f"[Telegram] Failed to send alert to chat_id {chat_id}: {e}")

