"""
Full-path test suite for PhoneINT Tier 2.

This sandbox's network policy blocks the real third-party APIs
(restcountries, HIBP, AbstractAPI), so every HTTP call is mocked here.
That's fine — this validates 100% of PhoneINT's own logic (parsing,
plugin dependency ordering, error/skip handling, the porting
comparison, JSON export). The mocked responses use the real response
shapes from each API's documentation, so behavior on your machine with
real keys will match what's tested here.

Run with: python3 tests/test_full_flow.py
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from phoneint_core.engine import run_investigation, parse_and_validate, NumberParseError
from phoneint_core.plugins import PLUGIN_REGISTRY


def fake_requests_get(url, *args, **kwargs):
    """Routes mocked responses based on which API the URL points to."""
    resp = MagicMock()

    if "countries.dev" in url:
        resp.status_code = 200
        resp.json.return_value = {
            "name": "India",
            "alpha2Code": "IN",
            "alpha3Code": "IND",
            "capital": "New Delhi",
            "region": "Asia",
            "subregion": "Southern Asia",
            "population": 1380004385,
            "area": 3287590,
            "currencies": [{"code": "INR", "name": "Indian rupee", "symbol": "₹"}],
            "callingCodes": ["91"],
            "topLevelDomain": [".in"],
            "borders": ["BGD", "BTN", "MMR", "CHN", "NPL", "PAK"],
            "flag": "https://countries.dev/flags/in.svg",
        }
        return resp

    if "haveibeenpwned.com" in url:
        resp.status_code = 200
        resp.json.return_value = [{"Name": "ExampleBreach2023"}]
        return resp

    if "abstractapi.com" in url:
        resp.status_code = 200
        resp.json.return_value = {
            "phone_number": "919876543210",
            "phone_carrier": {"name": "Reliance Jio", "line_type": "mobile", "mcc": 405, "mnc": 840},
            "phone_location": {
                "country_name": "India", "country_code": "IN", "region": "Delhi",
                "city": "New Delhi", "timezone": "Asia/Kolkata",
            },
            "phone_validation": {"is_valid": True, "line_status": "active", "is_voip": False},
            "phone_risk": {"risk_level": "low", "is_disposable": False, "is_abuse_detected": False},
            "phone_breaches": {"total_breaches": None, "date_first_breached": None,
                                "date_last_breached": None, "breached_domains": []},
        }
        return resp

    resp.status_code = 404
    resp.json.return_value = {}
    return resp


class TestParsing(unittest.TestCase):
    def test_valid_number(self):
        parsed = parse_and_validate("+919876543210")
        self.assertEqual(parsed.country_code, 91)

    def test_invalid_number_raises(self):
        with self.assertRaises(NumberParseError):
            parse_and_validate("not a number")

    def test_garbage_input_raises(self):
        with self.assertRaises(NumberParseError):
            parse_and_validate("123")


class TestEngineNoKeys(unittest.TestCase):
    """Simulates a fresh Windows install with no .env configured."""

    def setUp(self):
        os.environ.pop("HIBP_API_KEY", None)
        os.environ.pop("ABSTRACTAPI_PHONE_KEY", None)

    @patch("phoneint_core.plugins.geolocation.requests.get", side_effect=fake_requests_get)
    def test_all_plugins_present_and_correct_statuses(self, _mock):
        report = run_investigation("+919876543210")

        self.assertEqual(report.get("validation").status, "ok")
        self.assertEqual(report.get("geolocation").status, "ok")
        self.assertEqual(report.get("surface_analysis").status, "ok")
        self.assertEqual(report.get("footprint").status, "ok")
        self.assertEqual(report.get("breach_check").status, "skipped")
        self.assertEqual(report.get("reputation").status, "skipped")
        # porting depends on reputation; reputation skipped -> porting must skip too
        self.assertEqual(report.get("porting").status, "skipped")

    @patch("phoneint_core.plugins.geolocation.requests.get", side_effect=fake_requests_get)
    def test_validation_data_correct(self, _mock):
        report = run_investigation("+919876543210")
        data = report.get("validation").data
        self.assertEqual(data["E164 Format"], "+919876543210")
        self.assertEqual(data["Country Code"], "+91")
        self.assertEqual(data["Number Type"], "Mobile")

    @patch("phoneint_core.plugins.geolocation.requests.get", side_effect=fake_requests_get)
    def test_geolocation_data_correct(self, _mock):
        report = run_investigation("+919876543210")
        data = report.get("geolocation").data
        self.assertEqual(data["Country"], "India")
        self.assertEqual(data["Capital"], "New Delhi")
        self.assertIn("google.com/maps", data["Maps Link"])

    @patch("phoneint_core.plugins.geolocation.requests.get", side_effect=fake_requests_get)
    def test_footprint_links_well_formed(self, _mock):
        report = run_investigation("+919876543210")
        links = report.get("footprint").data["links"]
        self.assertTrue(links["WhatsApp Click-to-Chat"].startswith("https://wa.me/919876543210"))
        self.assertIn("truecaller.com", links["Truecaller Search"])

    @patch("phoneint_core.plugins.geolocation.requests.get", side_effect=fake_requests_get)
    def test_json_export_shape(self, _mock):
        report = run_investigation("+919876543210")
        as_dict = report.to_dict()
        json_str = json.dumps(as_dict)  # must not raise
        reparsed = json.loads(json_str)
        self.assertEqual(reparsed["target"], "+919876543210")
        self.assertIn("validation", reparsed["results"])


class TestEngineWithKeys(unittest.TestCase):
    """Simulates a fully configured .env — all plugins active."""

    def setUp(self):
        os.environ["HIBP_API_KEY"] = "fake-test-key"
        os.environ["ABSTRACTAPI_PHONE_KEY"] = "fake-test-key"

    def tearDown(self):
        os.environ.pop("HIBP_API_KEY", None)
        os.environ.pop("ABSTRACTAPI_PHONE_KEY", None)

    @patch("phoneint_core.plugins.reputation.requests.get", side_effect=fake_requests_get)
    @patch("phoneint_core.plugins.breach_check.requests.get", side_effect=fake_requests_get)
    @patch("phoneint_core.plugins.geolocation.requests.get", side_effect=fake_requests_get)
    def test_all_plugins_ok_with_keys(self, *_mocks):
        report = run_investigation("+919876543210")

        for name in ("validation", "geolocation", "surface_analysis", "footprint",
                     "breach_check", "reputation", "porting"):
            result = report.get(name)
            self.assertIsNotNone(result, f"{name} missing from report")
            self.assertEqual(result.status, "ok", f"{name} status: {result.status} / {result.error}")

    @patch("phoneint_core.plugins.reputation.requests.get", side_effect=fake_requests_get)
    @patch("phoneint_core.plugins.breach_check.requests.get", side_effect=fake_requests_get)
    @patch("phoneint_core.plugins.geolocation.requests.get", side_effect=fake_requests_get)
    def test_breach_data_correct(self, *_mocks):
        report = run_investigation("+919876543210")
        data = report.get("breach_check").data
        self.assertEqual(data["breaches_found"], 1)
        self.assertIn("ExampleBreach2023", data["breaches"])

    @patch("phoneint_core.plugins.reputation.requests.get", side_effect=fake_requests_get)
    @patch("phoneint_core.plugins.breach_check.requests.get", side_effect=fake_requests_get)
    @patch("phoneint_core.plugins.geolocation.requests.get", side_effect=fake_requests_get)
    def test_porting_detects_mismatch(self, *_mocks):
        # Mocked AbstractAPI carrier is "Reliance Jio"; +919876543210's static
        # phonenumbers carrier is "Airtel" -> mismatch -> should flag likely_ported=Yes
        report = run_investigation("+919876543210")
        data = report.get("porting").data
        self.assertEqual(data["likely_ported"], "Yes")
        self.assertEqual(data["live_carrier"], "Reliance Jio")


class TestPluginRegistry(unittest.TestCase):
    def test_all_plugins_have_unique_names(self):
        names = [p.name for p in PLUGIN_REGISTRY]
        self.assertEqual(len(names), len(set(names)), f"Duplicate plugin names: {names}")

    def test_all_dependencies_resolvable(self):
        names = {p.name for p in PLUGIN_REGISTRY}
        for p in PLUGIN_REGISTRY:
            for dep in p.depends_on:
                self.assertIn(dep, names, f"{p.name} depends on missing plugin '{dep}'")


if __name__ == "__main__":
    unittest.main(verbosity=2)