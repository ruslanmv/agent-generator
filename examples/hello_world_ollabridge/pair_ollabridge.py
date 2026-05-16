"""One-shot OllaBridge device pairing helper.

Usage:
    python pair_ollabridge.py GKEV-8985
    python pair_ollabridge.py GKEV-8985 --base https://ruslanmv-ollabridge.hf.space
    python pair_ollabridge.py GKEV-8985 --env .env

Exchanges the short-lived pairing code shown by OllaBridge Cloud for a
long-lived `device_token`, then writes (or updates) `OLLABRIDGE_TOKEN`,
`OLLABRIDGE_BASE_URL`, and `OLLABRIDGE_DEVICE_ID` in a `.env` file next
to this script (override with `--env`).

Pairing codes expire after ~10 minutes — get a fresh one from the
OllaBridge web console if the request fails with "Pairing code expired".
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://ruslanmv-ollabridge.hf.space"


def pair(base: str, code: str) -> dict[str, str]:
    """POST the pairing code; return {device_token, device_id}."""
    body = json.dumps({"code": code.strip()}).encode("utf-8")
    req = urllib.request.Request(
        f"{base.rstrip('/')}/device/pair-simple",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} from OllaBridge: {e.read().decode('utf-8', 'ignore')}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Network error reaching {base}: {e.reason}")

    if payload.get("status") != "ok" or not payload.get("device_token"):
        raise SystemExit(f"Pairing failed: {payload.get('error') or payload}")

    return {
        "OLLABRIDGE_TOKEN": payload["device_token"],
        "OLLABRIDGE_DEVICE_ID": payload.get("device_id") or "",
    }


def write_env(path: Path, values: dict[str, str]) -> None:
    """Upsert keys in a dotenv file, preserving anything already there."""
    existing: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            existing[k.strip()] = v.strip()
    existing.update(values)
    path.write_text("\n".join(f"{k}={v}" for k, v in existing.items()) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("code", help="Pairing code shown in the OllaBridge console (e.g. GKEV-8985).")
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"OllaBridge base URL (default: {DEFAULT_BASE}).")
    parser.add_argument("--env", default=".env", help="dotenv file to update (default: .env next to script).")
    args = parser.parse_args()

    env_path = Path(args.env)
    if not env_path.is_absolute():
        env_path = Path(__file__).parent / env_path

    print(f"→ Pairing code {args.code} with {args.base} …")
    values = pair(args.base, args.code)
    values["OLLABRIDGE_BASE_URL"] = args.base.rstrip("/")
    write_env(env_path, values)

    print(f"✓ Paired. Wrote {env_path}")
    print("  OLLABRIDGE_BASE_URL  =", values["OLLABRIDGE_BASE_URL"])
    print("  OLLABRIDGE_DEVICE_ID =", values["OLLABRIDGE_DEVICE_ID"] or "(not returned)")
    print("  OLLABRIDGE_TOKEN     =", values["OLLABRIDGE_TOKEN"][:8] + "…")
    print("\nNext: python hello_world.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
