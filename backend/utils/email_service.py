"""
email_service.py
-----------------
SMTP email alert service for AlgoShield AI monitoring system.

Responsibilities:
  - Send email notifications when a risky transaction is detected
  - Read SMTP_USER and SMTP_PASSWORD from environment variables
  - Use Gmail SMTP (ssl port 465) by default
  - Fail gracefully — never crash the monitoring loop

Usage:
    from utils.email_service import send_alert_email
    await send_alert_email(
        to_email="user@example.com",
        contract_address="ABCDE...",
        txn_id="XYZ123...",
        txn_type="axfer",
        risk_level="HIGH",
        label="RISKY"
    )
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Read credentials from environment — never hardcoded
SMTP_USER = os.getenv("EMAIL_USER", os.getenv("SMTP_USER", ""))
SMTP_PASSWORD = os.getenv("EMAIL_PASS", os.getenv("SMTP_PASSWORD", ""))
ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", f"AlgoShield AI <{SMTP_USER}>")

# SMTP settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))


def _build_email_body(contract_address: str, txn_id: str, txn_type: str,
                      risk_level: str, label: str) -> tuple[str, str]:
    """
    Build both plain-text and HTML versions of the alert email body.
    Returns (plain_text, html_text).
    """
    short_address = contract_address[:16] + "..." if len(contract_address) > 16 else contract_address
    short_txn = txn_id[:20] + "..." if len(txn_id) > 20 else txn_id

    plain = (
        f"AlgoShield AI - Smart Contract Alert\n"
        f"{'=' * 40}\n\n"
        f"A suspicious transaction has been detected on a monitored contract.\n\n"
        f"Contract Address : {contract_address}\n"
        f"Transaction ID   : {txn_id}\n"
        f"Transaction Type : {txn_type}\n"
        f"AI Risk Label    : {label}\n"
        f"Risk Level       : {risk_level}\n\n"
        f"Please review this contract activity immediately.\n\n"
        f"-- AlgoShield AI Monitoring System"
    )

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background:#0f0f1a; color:#e0e0f0; padding:24px;">
        <div style="max-width:600px; margin:auto; background:#1a1a2e; border-radius:12px;
                    border:1px solid #ff4d4d; padding:32px;">
          <h2 style="color:#ff4d4d; margin-top:0;">
            [!] AlgoShield AI &mdash; Smart Contract Alert
          </h2>
          <p style="color:#aaa; font-size:14px;">
            A suspicious transaction has been detected on a monitored contract.
          </p>
          <hr style="border-color:#333; margin:20px 0;" />
          <table style="width:100%; border-collapse:collapse; font-size:14px;">
            <tr>
              <td style="padding:8px; color:#888; width:40%;">Contract Address</td>
              <td style="padding:8px; color:#e0e0f0; word-break:break-all;">{contract_address}</td>
            </tr>
            <tr style="background:#111127;">
              <td style="padding:8px; color:#888;">Transaction ID</td>
              <td style="padding:8px; color:#e0e0f0; word-break:break-all;">{txn_id}</td>
            </tr>
            <tr>
              <td style="padding:8px; color:#888;">Transaction Type</td>
              <td style="padding:8px; color:#e0e0f0;">{txn_type}</td>
            </tr>
            <tr style="background:#111127;">
              <td style="padding:8px; color:#888;">AI Risk Label</td>
              <td style="padding:8px; color:#ff6b6b; font-weight:bold;">{label}</td>
            </tr>
            <tr>
              <td style="padding:8px; color:#888;">Risk Level</td>
              <td style="padding:8px;">
                <span style="background:#ff4d4d; color:#fff; padding:3px 10px;
                             border-radius:4px; font-weight:bold; font-size:13px;">
                  {risk_level}
                </span>
              </td>
            </tr>
          </table>
          <hr style="border-color:#333; margin:20px 0;" />
          <p style="color:#888; font-size:12px; margin:0;">
            This alert was generated automatically by the AlgoShield AI Monitoring System.
            Please review this contract's activity immediately.
          </p>
        </div>
      </body>
    </html>
    """
    return plain, html


def send_alert_email(to_email: str, contract_address: str, txn_id: str,
                     txn_type: str, risk_level: str, label: str) -> bool:
    """
    Send an alert email using Gmail SMTP with SSL.

    Returns True on success, False on failure.
    Never raises — errors are logged and the monitoring loop continues.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("[Email] SMTP_USER or SMTP_PASSWORD not set. Skipping email.")
        return False

    if not to_email or "@" not in to_email:
        logger.warning(f"[Email] Invalid recipient address: '{to_email}'. Skipping.")
        return False

    subject = "[AlgoShield AI] Smart Contract Alert Detected"
    plain_body, html_body = _build_email_body(
        contract_address, txn_id, txn_type, risk_level, label
    )

    try:
        # Build MIME multipart message (plain + HTML fallback)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = ALERT_FROM_EMAIL
        msg["To"] = to_email

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Send via Gmail SMTP over SSL
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        logger.info(
            f"[Email] Alert email sent to {to_email} | "
            f"TXN {txn_id[:16]}... | risk_level={risk_level}"
        )
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "[Email] SMTP Authentication failed. "
            "Ensure SMTP_USER and SMTP_PASSWORD (App Password) are correct."
        )
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"[Email] Recipient refused: {to_email}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"[Email] SMTP error while sending to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"[Email] Unexpected error while sending email: {e}")
        return False
