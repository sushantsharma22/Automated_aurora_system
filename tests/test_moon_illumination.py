import sys
import pathlib
import datetime as dt
import requests

# Ensure project root is on sys.path so tests can import the `aurora` package
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aurora import fetch


def test_moon_api_success(monkeypatch):
    class DummyResp:
        def raise_for_status(self):
            return None

        def json(self):
            return [{'Illumination': '55.0'}]

    def fake_get(url, timeout=10, verify=True):
        return DummyResp()

    monkeypatch.setattr(requests, 'get', fake_get)

    val = fetch.moon_illumination(dt.date(2025, 8, 26))
    assert isinstance(val, float)
    assert abs(val - 55.0) < 1e-6


def test_moon_api_ssl_failure_fallback(monkeypatch):
    def fake_get(url, timeout=10, verify=True):
        raise requests.exceptions.SSLError("ssl")

    monkeypatch.setattr(requests, 'get', fake_get)

    val = fetch.moon_illumination(dt.datetime(2025, 8, 26, 0, 0))
    assert isinstance(val, float)
    assert 0.0 <= val <= 100.0
