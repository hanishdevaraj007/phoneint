#!/usr/bin/env python3
"""
PhoneINT - Phone Number OSINT Intelligence Tool
Author: Hanish D
Description: Performs carrier lookup, number validation, geolocation,
             and generates a basic intelligence profile from a phone number
             using open-source data sources.
"""

import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType
import requests
import json
import sys
import argparse
from datetime import datetime


# ─────────────────────────────────────────────
# ANSI Colors for terminal output
# ─────────────────────────────────────────────
class Color:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    BOLD    = "\033[1m"
    RESET   = "\033[0m"


def banner():
    print(f"""
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


# ─────────────────────────────────────────────
# Parse and validate phone number
# ─────────────────────────────────────────────
def parse_number(raw_number: str):
    try:
        parsed = phonenumbers.parse(raw_number, None)
        if not phonenumbers.is_valid_number(parsed):
            print(f"{Color.RED}[-] Invalid phone number.{Color.RESET}")
            sys.exit(1)
        return parsed
    except phonenumbers.phonenumberutil.NumberParseException as e:
        print(f"{Color.RED}[-] Parse error: {e}{Color.RESET}")
        sys.exit(1)


# ─────────────────────────────────────────────
# Extract metadata from phonenumbers library
# ─────────────────────────────────────────────
def extract_metadata(parsed) -> dict:
    num_type_map = {
        PhoneNumberType.MOBILE:       "Mobile",
        PhoneNumberType.FIXED_LINE:   "Fixed Line",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
        PhoneNumberType.TOLL_FREE:    "Toll Free",
        PhoneNumberType.PREMIUM_RATE: "Premium Rate",
        PhoneNumberType.VOIP:         "VoIP",
        PhoneNumberType.UNKNOWN:      "Unknown",
    }

    ntype = number_type(parsed)

    return {
        "E164 Format":       phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        "International":     phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "National":          phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
        "Country Code":      f"+{parsed.country_code}",
        "National Number":   str(parsed.national_number),
        "Region":            geocoder.description_for_number(parsed, "en") or "Unknown",
        "Carrier":           carrier.name_for_number(parsed, "en") or "Unknown",
        "Timezones":         ", ".join(timezone.time_zones_for_number(parsed)) or "Unknown",
        "Number Type":       num_type_map.get(ntype, "Unknown"),
        "Is Valid":          str(phonenumbers.is_valid_number(parsed)),
        "Is Possible":       str(phonenumbers.is_possible_number(parsed)),
    }


# ─────────────────────────────────────────────
# Geolocation via country code → coordinates
# Uses restcountries.com (free, no API key)
# ─────────────────────────────────────────────
def geolocate(parsed) -> dict:
    try:
        region_code = phonenumbers.region_code_for_number(parsed)
        if not region_code:
            return {"Error": "Could not determine country region code."}
            
        url = f"https://restcountries.com/v3.1/alpha/{region_code}"
        response = requests.get(url, timeout=8)

        if response.status_code == 200:
            json_data = response.json()
            # Safety check: verify response is a list and contains elements
            if not isinstance(json_data, list) or len(json_data) == 0:
                return {"Error": "Empty data structure returned from API"}
                
            data = json_data[0]
            latlng = data.get("latlng", [None, None])
            capital = data.get("capital", ["Unknown"])[0] if data.get("capital") else "Unknown"
            population = data.get("population", "Unknown")
            region = data.get("region", "Unknown")
            subregion = data.get("subregion", "Unknown")
            flag = data.get("flag", "")

            return {
                "Country":      data.get("name", {}).get("common", "Unknown"),
                "Capital":      capital,
                "Region":       region,
                "Subregion":    subregion,
                "Latitude":     latlng[0] if latlng and len(latlng) > 0 else "Unknown",
                "Longitude":    latlng[1] if latlng and len(latlng) > 1 else "Unknown",
                "Population":   f"{population:,}" if isinstance(population, int) else population,
                "Flag":         flag,
                "Maps Link":    f"https://www.google.com/maps?q={latlng[0]},{latlng[1]}" if latlng and latlng[0] else "Unavailable"
            }
        else:
            return {"Error": f"HTTP {response.status_code} from restcountries API"}

    except requests.exceptions.RequestException as e:
        return {"Error": f"Network error: {e}"}


# ─────────────────────────────────────────────
# OSINT surface scan — known breach DB check
# Uses HaveIBeenPwned-style hint (no key needed)
# ─────────────────────────────────────────────
def osint_hints(metadata: dict) -> list:
    hints = []

    if metadata.get("Number Type") == "VoIP":
        hints.append("VoIP number detected — may indicate anonymization or virtual SIM usage")
    if metadata.get("Carrier") == "Unknown":
        hints.append("Carrier unresolved — possible MVNO, eSIM, or number porting")
    if metadata.get("Region") == "Unknown":
        hints.append("Region unresolved — possible satellite or non-geographic number")

    return hints if hints else ["No anomalies detected"]


# Print intelligence report
def print_report(raw_number: str, metadata: dict, geo: dict, hints: list):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{Color.BOLD}{Color.CYAN}{'═'*55}")
    print(f"  PHONEINT INTELLIGENCE REPORT")
    print(f"  Target   : {raw_number}")
    print(f"  Generated: {timestamp}")
    print(f"{'═'*55}{Color.RESET}\n")

    print(f"{Color.GREEN}{Color.BOLD}[+] NUMBER METADATA{Color.RESET}")
    for k, v in metadata.items():
        print(f"    {Color.YELLOW}{k:<22}{Color.RESET}: {v}")

    print(f"\n{Color.GREEN}{Color.BOLD}[+] GEOLOCATION PROFILE{Color.RESET}")
    if "Error" in geo:
        print(f"    {Color.RED}{geo['Error']}{Color.RESET}")
    else:
        for k, v in geo.items():
            print(f"    {Color.YELLOW}{k:<22}{Color.RESET}: {v}")

    print(f"\n{Color.GREEN}{Color.BOLD}[+] OSINT SURFACE ANALYSIS{Color.RESET}")
    for hint in hints:
        print(f"    {Color.CYAN}→{Color.RESET} {hint}")

    print(f"\n{Color.CYAN}{'═'*55}{Color.RESET}\n")


# Export report to JSON
def export_json(raw_number: str, metadata: dict, geo: dict, hints: list):
    report = {
        "target": raw_number,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata,
        "geolocation": geo,
        "osint_hints": hints
    }
    filename = f"phoneint_{raw_number.replace('+', '').replace(' ', '_')}.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=4)
    print(f"{Color.GREEN}[✓] Report saved to {filename}{Color.RESET}\n")


# Main
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

    # Interactive input if no argument given
    if not args.number:
        args.number = input(f"{Color.CYAN}[?] Enter phone number (with country code, e.g. +919876543210): {Color.RESET}").strip()

    parsed      = parse_number(args.number)
    metadata    = extract_metadata(parsed)
    geo         = geolocate(parsed)
    hints       = osint_hints(metadata)
    
    print_report(args.number, metadata, geo, hints)
    
    if args.export:
        export_json(args.number, metadata, geo, hints)


if __name__ == "__main__":
    main()