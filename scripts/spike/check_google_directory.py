#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

READ_ONLY_SCOPE = "https://www.googleapis.com/auth/admin.directory.user.readonly"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only Google Directory check that prints sanitized OU fields only."
    )
    parser.add_argument(
        "--emails",
        nargs="+",
        required=True,
        help="Corporate emails to look up.",
    )
    parser.add_argument(
        "--admin-subject",
        default=os.getenv("GOOGLE_SPIKE_ADMIN_SUBJECT", ""),
        help="Admin user email for domain-wide delegation. Defaults to GOOGLE_SPIKE_ADMIN_SUBJECT.",
    )
    parser.add_argument(
        "--credentials-file",
        default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        help="Service account JSON path. Defaults to GOOGLE_APPLICATION_CREDENTIALS.",
    )
    return parser.parse_args()


def _sanitize_user(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "primaryEmail": str(payload.get("primaryEmail", "")).strip(),
        "orgUnitPath": str(payload.get("orgUnitPath", "")).strip(),
    }


def main() -> int:
    args = _parse_args()

    if not args.credentials_file:
        print("ERROR: missing credentials file (set --credentials-file or GOOGLE_APPLICATION_CREDENTIALS)", file=sys.stderr)
        return 2

    if not args.admin_subject:
        print("ERROR: missing admin subject (set --admin-subject or GOOGLE_SPIKE_ADMIN_SUBJECT)", file=sys.stderr)
        return 2

    try:
        from google.oauth2 import service_account  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
        from googleapiclient.errors import HttpError  # type: ignore
    except ModuleNotFoundError as exc:
        print(
            "ERROR: missing Google API client dependencies (google-api-python-client and google-auth)",
            file=sys.stderr,
        )
        print(f"DETAIL: {exc}", file=sys.stderr)
        return 2

    creds = service_account.Credentials.from_service_account_file(
        args.credentials_file,
        scopes=[READ_ONLY_SCOPE],
    ).with_subject(args.admin_subject)

    service = build("admin", "directory_v1", credentials=creds, cache_discovery=False)
    users_resource = service.users()

    for email in args.emails:
        try:
            payload = users_resource.get(userKey=email, projection="basic").execute()
        except HttpError as exc:
            status = getattr(getattr(exc, "resp", None), "status", None)
            if status == 404:
                print(json.dumps({"primaryEmail": email, "orgUnitPath": "", "status": "not_found"}))
                continue
            print(f"ERROR: directory lookup failed for {email}: {exc}", file=sys.stderr)
            return 3

        sanitized = _sanitize_user(payload)
        sanitized["status"] = "ok"
        print(json.dumps(sanitized, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
