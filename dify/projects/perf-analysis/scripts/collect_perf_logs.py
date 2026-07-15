#!/usr/bin/env python3
"""
Dify Workflow Performance Log Collector

Collects [PERF_TIMING] logs from Dify Docker containers and saves them
for analysis. Compatible with Python 3.6+, no third-party dependencies.

Usage:
    python3 collect_perf_logs.py                          # Collect from running containers
    python3 collect_perf_logs.py --since 1h               # Logs from last hour
    python3 collect_perf_logs.py --since 2026-06-05T10:00:00  # Logs since timestamp
    python3 collect_perf_logs.py --output perf.json       # Custom output file
    python3 collect_perf_logs.py --container api worker   # Specific containers
"""

from __future__ import print_function

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

PERF_PATTERN = re.compile(r"\[PERF_TIMING\]\s+(.+)")

CONTAINER_NAMES = [
    "dify-api-1",
    "dify-worker-1",
    "dify-worker_beat-1",
]


def parse_perf_line(line):
    """Parse a [PERF_TIMING] log line into structured data."""
    match = PERF_PATTERN.search(line)
    if not match:
        return None

    content = match.group(1).strip()

    entry = {"raw": content}

    parts = content.split(" | ")
    for part in parts:
        part = part.strip()
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        key = key.strip()
        value = value.strip()

        if key in ("elapsed", "total_elapsed", "latency",
                    "time_to_first_token", "time_to_generate", "timestamp"):
            try:
                value = float(value)
            except ValueError:
                pass
        elif key in ("prompt_tokens", "completion_tokens", "total_tokens",
                      "node_count", "exceptions"):
            try:
                value = int(value)
            except ValueError:
                pass
        elif key in ("has_error",):
            value = value.lower() == "true"

        entry[key] = value

    return entry


def collect_from_docker(containers, since=None, until=None):
    """Collect PERF_TIMING logs from docker containers."""
    entries = []

    for container in containers:
        cmd = ["docker", "logs", container, "--timestamps"]
        if since:
            cmd.extend(["--since", since])
        if until:
            cmd.extend(["--until", until])

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            stdout, stderr = proc.communicate(timeout=120)

            if proc.returncode != 0:
                print("Warning: docker logs failed for {}: {}".format(
                    container, stderr.strip()), file=sys.stderr)
                continue

            for line in stdout.splitlines():
                entry = parse_perf_line(line)
                if entry:
                    entry["_container"] = container
                    entries.append(entry)

        except subprocess.TimeoutExpired:
            print("Warning: timeout collecting logs from {}".format(container),
                  file=sys.stderr)
            proc.kill()
        except OSError as e:
            print("Warning: cannot run docker for {}: {}".format(container, e),
                  file=sys.stderr)

    return entries


def collect_from_file(filepath):
    """Collect PERF_TIMING logs from a log file."""
    entries = []
    with open(filepath, "r") as f:
        for line in f:
            entry = parse_perf_line(line)
            if entry:
                entry["_source"] = filepath
                entries.append(entry)
    return entries


def main():
    parser = argparse.ArgumentParser(
        description="Collect Dify workflow performance timing logs"
    )
    parser.add_argument(
        "--output", "-o",
        default="perf_logs.json",
        help="Output JSON file path (default: perf_logs.json)",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Collect logs since (e.g. '1h', '30m', '2026-06-05T10:00:00')",
    )
    parser.add_argument(
        "--until",
        default=None,
        help="Collect logs until (same format as --since)",
    )
    parser.add_argument(
        "--containers", "-c",
        nargs="+",
        default=CONTAINER_NAMES,
        help="Docker container names to collect from",
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Read from a log file instead of Docker containers",
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty-print JSON output",
    )

    args = parser.parse_args()

    if args.file:
        print("Reading from file: {}".format(args.file), file=sys.stderr)
        entries = collect_from_file(args.file)
    else:
        print("Collecting from containers: {}".format(
            ", ".join(args.containers)), file=sys.stderr)
        entries = collect_from_docker(
            args.containers,
            since=args.since,
            until=args.until,
        )

    indent = 2 if args.pretty else None
    with open(args.output, "w") as f:
        json.dump(entries, f, indent=indent, sort_keys=True)

    print("Collected {} PERF_TIMING entries -> {}".format(
        len(entries), args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
