#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

"""
DingTalk message sender script.
Send text/markdown messages to DingTalk groups or users via Robot API.
"""

import argparse
import os
import sys

from bub_skills.dingtalk.send import send_message


def main() -> None:
    parser = argparse.ArgumentParser(description="Send message to DingTalk")
    parser.add_argument("--chat-id", "-c", required=True, help="Target chat ID (group:xxx or user_id)")
    parser.add_argument("--content", "-m", required=True, help="Message content (markdown)")
    parser.add_argument("--title", "-t", default="Bub Reply", help="Message title")
    parser.add_argument(
        "--client-id",
        default=os.environ.get("BUB_DINGTALK_CLIENT_ID"),
        help="DingTalk app client_id",
    )
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("BUB_DINGTALK_CLIENT_SECRET"),
        help="DingTalk app client_secret",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Disable SSL certificate verification",
    )
    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        print("Error: BUB_DINGTALK_CLIENT_ID and BUB_DINGTALK_CLIENT_SECRET are required")
        sys.exit(1)

    try:
        send_message(
            args.client_id,
            args.client_secret,
            args.chat_id,
            args.content,
            title=args.title,
            verify=not args.no_verify,
        )
        print(f"Message sent to {args.chat_id}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
