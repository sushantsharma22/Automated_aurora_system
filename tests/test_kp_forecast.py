import sys
import pathlib
import requests

# Ensure project root is on sys.path so tests can import the `aurora` package
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aurora import fetch


def test_kp_forecast_parses_dict_rows(monkeypatch):
    class DummyResp:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    "time_tag": "2026-04-19T18:00:00",
                    "kp": 3.67,
                    "observed": "observed",
                    "noaa_scale": None,
                },
                {
                    "time_tag": "2026-04-19T21:00:00",
                    "kp": 5.0,
                    "observed": "predicted",
                    "noaa_scale": "G1",
                },
            ]

    def fake_get(url, timeout=10):
        return DummyResp()

    monkeypatch.setattr(requests, "get", fake_get)

    out = fetch.kp_forecast()
    assert len(out) == 1
    kp, when = out[0]
    assert kp == 5.0
    assert when.tzinfo is not None
