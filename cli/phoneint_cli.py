#!/usr/bin/env python3
"""
PhoneINT CLI - thin wrapper over phoneint_core.

All logic now lives in phoneint_core (engine + plugins). This file is
responsible only for: argument parsing, input prompting, and printing.
Behavior/output is intended to match the original single-file script.
"""

import sys
import os
import json
import argparse
from datetime import datetime

# Allow running this file directly (python cli/phoneint_cli.py) by adding
# the project root to the path so `phoneint_core` is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from phoneint_core.engine import run_investigation, NumberParseError
from phoneint_core.models import InvestigationReport


class Color:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"


def banner():
    print(f"""
{Color.CYAN}{Color.BOLD}
██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗██╗███╗   ██╗████████╗
██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝██║████╗  ██║╚══██╔══╝
██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  ██║██╔██╗ ██║   ██║
██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  ██║██║╚██╗██║   ██║
██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗██║██║ ╚████║   ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
{Color.RESET}
{Color.YELLOW}  Phone Number OSINT Intelligence Tool | by Hanish D{Color.RESET}
{Color.RED}  [!] For educational and authorized use only{Color.RESET}
    """)


def print_report(report: InvestigationReport):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{Color.BOLD}{Color.CYAN}{'═'*55}")
    print(f"  PHONEINT INTELLIGENCE REPORT")
    print(f"  Target   : {report.target}")
    print(f"  Generated: {timestamp}")
    print(f"{'═'*55}{Color.RESET}\n")

    validation = report.get("validation")
    print(f"{Color.GREEN}{Color.BOLD}[+] NUMBER METADATA{Color.RESET}")
    if validation and validation.status == "ok":
        for k, v in validation.data.items():
            print(f"    {Color.YELLOW}{k:<22}{Color.RESET}: {v}")
    else:
        print(f"    {Color.RED}{validation.error if validation else 'No data'}{Color.RESET}")

    geo = report.get("geolocation")
    print(f"\n{Color.GREEN}{Color.BOLD}[+] GEOLOCATION PROFILE{Color.RESET}")
    if geo and geo.status == "ok":
        for k, v in geo.data.items():
            print(f"    {Color.YELLOW}{k:<22}{Color.RESET}: {v}")
    else:
        print(f"    {Color.RED}{geo.error if geo else 'No data'}{Color.RESET}")

    surface = report.get("surface_analysis")
    print(f"\n{Color.GREEN}{Color.BOLD}[+] OSINT SURFACE ANALYSIS{Color.RESET}")
    if surface and surface.status == "ok":
        for hint in surface.data.get("hints", []):
            print(f"    {Color.CYAN}→{Color.RESET} {hint}")
    else:
        print(f"    {Color.RED}{surface.error if surface else 'No data'}{Color.RESET}")

    print(f"\n{Color.CYAN}{'═'*55}{Color.RESET}\n")


def export_json(report: InvestigationReport):
    filename = f"phoneint_{report.target.replace('+', '').replace(' ', '_')}.json"
    with open(filename, "w") as f:
        json.dump(report.to_dict(), f, indent=4)
    print(f"{Color.GREEN}[✓] Report saved to {filename}{Color.RESET}\n")


def main():
    banner()

    parser = argparse.ArgumentParser(
        description="PhoneINT — Phone Number OSINT Intelligence Tool"
    )
    parser.add_argument(
        "number",
        nargs="?",
        help="Target phone number in E164 format (e.g. +919876543210)"
    )
    parser.add_argument(
        "--export", "-e",
        action="store_true",
        help="Export report to JSON file"
    )
    args = parser.parse_args()

    if not args.number:
        args.number = input(
            f"{Color.CYAN}[?] Enter phone number (with country code, e.g. +919876543210): {Color.RESET}"
        ).strip()

    try:
        report = run_investigation(args.number)
    except NumberParseError as e:
        print(f"{Color.RED}[-] {e}{Color.RESET}")
        sys.exit(1)

    print_report(report)

    if args.export:
        export_json(report)


if __name__ == "__main__":
    main()