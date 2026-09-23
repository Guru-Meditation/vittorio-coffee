"""Set Gmail SMTP_PASSWORD on Render (one-time).

Requires:
  RENDER_API_KEY — from https://dashboard.render.com/u/settings#api-keys
  SMTP_PASSWORD  — Gmail App Password for pantzosantonis@gmail.com

Usage (PowerShell):
  $env:RENDER_API_KEY = "rnd_..."
  $env:SMTP_PASSWORD = (Get-Clipboard -Raw).Trim()
  python tools/set_render_smtp.py
"""

import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import quote

SERVICE_ID = "srv-dapsc76gekts73f1kjb0"
ENV_KEY = "SMTP_PASSWORD"


def main():
    api_key = os.environ.get("RENDER_API_KEY", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    if not api_key or "PASTE" in api_key or api_key == "rnd_...":
        sys.exit(
            "Set RENDER_API_KEY to your real key from Render → Account Settings → API Keys "
            "(starts with rnd_, not the placeholder text)."
        )
    if not password:
        sys.exit("Set SMTP_PASSWORD to your Gmail App Password (copy it first).")

    url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{quote(ENV_KEY)}"
    payload = json.dumps({"value": password}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        if err.code == 401:
            sys.exit(
                "Render API error 401 Unauthorized — your RENDER_API_KEY is wrong or revoked. "
                "Create a new key in Account Settings → API Keys and try again."
            )
        sys.exit(f"Render API error {err.code}: {detail}")

    print("SMTP_PASSWORD saved on Render. Wait for redeploy, then test an order email.")
    if body.strip():
        print(body)


if __name__ == "__main__":
    main()
