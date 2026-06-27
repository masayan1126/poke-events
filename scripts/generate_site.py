#!/usr/bin/env python3
"""Codex-friendly wrapper: validate JSON, generate HTML, validate HTML."""

import argparse
import os
import subprocess
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run(args):
    subprocess.run(args, cwd=ROOT, check=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate the pokeca event static site")
    parser.add_argument("events_json", help="イベント収集・行動プラン生成済みJSON")
    parser.add_argument("--output", default="index.html", help="生成先HTML。既定値: index.html")
    parser.add_argument("--require-future-target", action="store_true", help="対象日が今日以降であることを要求する")
    parser.add_argument("--skip-html-validation", action="store_true", help="HTML検証を省略する")
    return parser.parse_args()


def main():
    args = parse_args()
    output = os.path.abspath(os.path.join(ROOT, args.output))

    validate_cmd = [sys.executable, "scripts/validate_event_json.py", args.events_json]
    if args.require_future_target:
        validate_cmd.append("--require-future-target")
    run(validate_cmd)
    run([sys.executable, "scripts/generate_page.py", args.events_json, "--output", output])
    if not args.skip_html_validation:
        run([sys.executable, "scripts/validate_generated_site.py", output])

    print(f"Generated site: {output}")


if __name__ == "__main__":
    main()
