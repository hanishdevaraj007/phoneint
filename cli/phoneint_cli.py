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

# colorama translates ANSI escape codes into Windows console API calls.
# Without this, raw \033[...m codes print as garbage on cmd.exe/older
# PowerShell. autoreset=True means we don't have to worry about a
# crash leaving the terminal stuck in a color.
from colorama import init as colorama_init
colorama_init(autoreset=True)

# Load API keys from a .env file in the project root if present, so
# Windows users don't have to set environment variables manually every
# session. Safe no-op if python-dotenv isn't installed or .env is absent.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

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

    footprint = report.get("footprint")
    print(f"\n{Color.GREEN}{Color.BOLD}[+] DIGITAL FOOTPRINT / PIVOT LINKS{Color.RESET}")
    if footprint and footprint.status == "ok":
        for k, v in footprint.data.get("links", {}).items():
            print(f"    {Color.YELLOW}{k:<26}{Color.RESET}: {v}")
    else:
        print(f"    {Color.RED}{footprint.error if footprint else 'No data'}{Color.RESET}")

    breach = report.get("breach_check")
    print(f"\n{Color.GREEN}{Color.BOLD}[+] BREACH EXPOSURE (HaveIBeenPwned){Color.RESET}")
    if breach and breach.status == "ok":
        count = breach.data.get("breaches_found", 0)
        if count == 0:
            print(f"    {Color.CYAN}→{Color.RESET} No known breaches")
        else:
            print(f"    {Color.RED}→ {count} breach(es) found:{Color.RESET}")
            for name in breach.data.get("breaches", []):
                print(f"        - {name}")
    elif breach and breach.status == "skipped":
        print(f"    {Color.YELLOW}[skipped] {breach.error}{Color.RESET}")
    else:
        print(f"    {Color.RED}{breach.error if breach else 'No data'}{Color.RESET}")

    reputation = report.get("reputation")
    print(f"\n{Color.GREEN}{Color.BOLD}[+] REPUTATION / VALIDATION (AbstractAPI){Color.RESET}")
    if reputation and reputation.status == "ok":
        for k, v in reputation.data.items():
            print(f"    {Color.YELLOW}{k:<26}{Color.RESET}: {v}")
    elif reputation and reputation.status == "skipped":
        print(f"    {Color.YELLOW}[skipped] {reputation.error}{Color.RESET}")
    else:
        print(f"    {Color.RED}{reputation.error if reputation else 'No data'}{Color.RESET}")

    porting = report.get("porting")
    print(f"\n{Color.GREEN}{Color.BOLD}[+] PORTING ANALYSIS (static vs live carrier){Color.RESET}")
    if porting and porting.status == "ok":
        for k, v in porting.data.items():
            print(f"    {Color.YELLOW}{k:<26}{Color.RESET}: {v}")
    elif porting and porting.status == "skipped":
        print(f"    {Color.YELLOW}[skipped] {porting.error}{Color.RESET}")
    else:
        print(f"    {Color.RED}{porting.error if porting else 'No data'}{Color.RESET}")

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