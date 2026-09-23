"""Create or update SMTP_PASSWORD on the vittorio-coffee Render web service.

Requires:
  RENDER_API_KEY — https://dashboard.render.com/u/settings#api-keys
  SMTP_PASSWORD  — Gmail App Password (spaces OK)

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
BASE = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars"


def _request(api_key, method, url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw.strip() else {}


def list_env_keys(api_key):
    keys = []
    cursor = None
    while True:
        url = BASE + "?limit=100"
        if cursor:
            url += f"&cursor={quote(cursor)}"
        page = _request(api_key, "GET", url)
        for item in page:
            env = item.get("envVar") or item
            key = env.get("key")
            if key:
                keys.append(key)
        cursor = page[-1].get("cursor") if page else None
        if not cursor:
            break
    return keys


def upsert_env(api_key, value):
    encoded_key = quote(ENV_KEY)
    try:
        _request(
            api_key,
            "PUT",
            f"{BASE}/{encoded_key}",
            {"value": value},
        )
        return "updated"
    except urllib.error.HTTPError as err:
        if err.code not in (404, 405):
            raise
    _request(api_key, "POST", BASE, {"envVar": {"key": ENV_KEY, "value": value}})
    return "created"


def trigger_deploy(api_key):
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
    try:
        _request(api_key, "POST", url, {"clearCache": "do_not_clear"})
    except urllib.error.HTTPError:
        pass


def main():
    api_key = os.environ.get("RENDER_API_KEY", "").strip()
    password = (os.environ.get("SMTP_PASSWORD", "") or "").strip().replace(" ", "")
    if not api_key or "PASTE" in api_key or api_key == "rnd_...":
        sys.exit("Set RENDER_API_KEY (Render → Account Settings → API Keys).")
    if len(password) < 16:
        sys.exit("Set SMTP_PASSWORD to your 16-character Gmail App Password.")

    try:
        before = list_env_keys(api_key)
        action = upsert_env(api_key, password)
        after = list_env_keys(api_key)
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        if err.code == 401:
            sys.exit("Render API 401 — RENDER_API_KEY is wrong or revoked.")
        sys.exit(f"Render API error {err.code}: {detail}")

    print(f"SMTP_PASSWORD {action} on service {SERVICE_ID}.")
    print(f"Env keys now ({len(after)}): {', '.join(sorted(after))}")
    if ENV_KEY not in after:
        print("WARNING: SMTP_PASSWORD still not listed — check service ID in dashboard URL.")
    trigger_deploy(api_key)
    print("Deploy triggered. After Live, check https://vittorio-coffee.onrender.com/health/mail")


if __name__ == "__main__":
    main()
