import html
import logging
import os

import requests

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM = os.environ.get("GROWHUB_EMAIL_FROM") or "GrowHub <onboarding@resend.dev>"
TIMEOUT_SECONDS = 10

logger = logging.getLogger("uvicorn.error")


class EmailError(Exception):
    pass


def is_configured() -> bool:
    return bool(RESEND_API_KEY)


def send_email(to: str, subject: str, html_body: str, text_body: str) -> None:
    if not is_configured():
        logger.warning("RESEND_API_KEY is not set, so this email was not sent.\nTo: %s\n%s", to, text_body)
        return
    try:
        response = requests.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": EMAIL_FROM, "to": [to], "subject": subject, "html": html_body, "text": text_body},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        raise EmailError(f"Could not reach Resend: {error}") from error
    if not response.ok:
        raise EmailError(f"Resend rejected the email ({response.status_code}): {response.text[:300]}")


def send_verification_email(to: str, link: str) -> None:
    safe_link = html.escape(link, quote=True)
    html_body = f"""\
<div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; color: #17313b;">
  <h1 style="color: #004b2d; font-size: 24px;">Confirm your GrowHub account</h1>
  <p>Click the button below to verify your email and start monitoring your plants.</p>
  <p style="margin: 28px 0;">
    <a href="{safe_link}" style="background: #004b2d; color: #ffffff; padding: 12px 22px; border-radius: 999px; text-decoration: none; font-weight: bold;">Verify email</a>
  </p>
  <p style="color: #617178; font-size: 14px;">Or paste this link into your browser:<br><a href="{safe_link}" style="color: #004b2d;">{safe_link}</a></p>
  <p style="color: #617178; font-size: 14px;">The link expires in 24 hours. If you didn't create a GrowHub account, you can ignore this email.</p>
</div>"""
    text_body = (
        "Confirm your GrowHub account\n\n"
        f"Open this link to verify your email:\n{link}\n\n"
        "The link expires in 24 hours. If you didn't create a GrowHub account, you can ignore this email."
    )
    send_email(to, "Verify your GrowHub email", html_body, text_body)
