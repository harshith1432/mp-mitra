"""
Unit tests for the MP Mitra enterprise update system.
Tests cover: latest version, no update, invalid repo, 404, 403,
             timeout, offline, no releases, and version comparison.

Run:
    python -m pytest backend/tests/test_updater.py -v
"""

import json
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import urllib.error

# Ensure the backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.updater import (
    _version_tuple,
    is_update_available,
    _UpdateError,
    _http_get_json,
    _extract_manifest,
    display_check_update,
    get_local_version,
    auto_check_on_start,
)


# ─── Helper: mock HTTP response ───────────────────────────────────────────────

def _make_release(tag: str, body: str = "- Bug fixes", has_zip: bool = False) -> dict:
    """Creates a fake GitHub Release API response."""
    assets = []
    if has_zip:
        assets.append({
            "name": f"MPMitraSetup-windows.zip",
            "browser_download_url": f"https://example.com/dl/{tag}.zip",
        })
    return {
        "tag_name": tag,
        "name": f"MP Mitra {tag}",
        "body": body,
        "published_at": "2026-07-10T00:00:00Z",
        "assets": assets,
    }


def _mock_urlopen(release_data: dict):
    """Returns a context manager mock that yields a fake HTTP response."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(release_data).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ─── Version Comparison Tests ─────────────────────────────────────────────────

class TestVersionComparison(unittest.TestCase):

    def test_version_tuple_basic(self):
        self.assertEqual(_version_tuple("1.2.3"), (1, 2, 3))

    def test_version_tuple_with_v_prefix(self):
        self.assertEqual(_version_tuple("v2.0.0"), (2, 0, 0))

    def test_version_tuple_with_V_prefix(self):
        self.assertEqual(_version_tuple("V1.0.1"), (1, 0, 1))

    def test_version_tuple_invalid_returns_zeros(self):
        self.assertEqual(_version_tuple("invalid"), (0, 0, 0))

    def test_update_available_when_remote_newer(self):
        self.assertTrue(is_update_available("1.0.0", "1.0.1"))

    def test_no_update_when_same_version(self):
        self.assertFalse(is_update_available("1.0.0", "1.0.0"))

    def test_no_update_when_local_is_newer(self):
        self.assertFalse(is_update_available("1.2.0", "1.1.9"))

    def test_major_version_bump_detected(self):
        self.assertTrue(is_update_available("1.9.9", "2.0.0"))

    def test_minor_version_bump_detected(self):
        self.assertTrue(is_update_available("1.0.5", "1.1.0"))

    def test_patch_version_bump_detected(self):
        self.assertTrue(is_update_available("1.0.0", "1.0.1"))


# ─── HTTP GET Tests ───────────────────────────────────────────────────────────

class TestHttpGetJson(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_success_returns_dict(self, mock_open):
        mock_open.return_value = _mock_urlopen({"tag_name": "v1.0.1"})
        result = _http_get_json("https://api.github.com/test")
        self.assertEqual(result["tag_name"], "v1.0.1")

    @patch("urllib.request.urlopen")
    def test_404_raises_not_found(self, mock_open):
        mock_open.side_effect = urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs={}, fp=None
        )
        with self.assertRaises(_UpdateError) as ctx:
            _http_get_json("https://api.github.com/test")
        self.assertEqual(ctx.exception.code, "not_found")

    @patch("urllib.request.urlopen")
    def test_403_raises_forbidden(self, mock_open):
        mock_fp = MagicMock()
        mock_fp.read.return_value = b'{"message":"Forbidden"}'
        mock_open.side_effect = urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs={}, fp=mock_fp
        )
        with self.assertRaises(_UpdateError) as ctx:
            _http_get_json("https://api.github.com/test")
        self.assertIn(ctx.exception.code, ("forbidden", "rate_limit"))

    @patch("urllib.request.urlopen")
    def test_timeout_raises_timeout(self, mock_open):
        import socket
        mock_open.side_effect = urllib.error.URLError(reason="timed out")
        with self.assertRaises(_UpdateError) as ctx:
            _http_get_json("https://api.github.com/test")
        self.assertEqual(ctx.exception.code, "timeout")

    @patch("urllib.request.urlopen")
    def test_no_network_raises_no_network(self, mock_open):
        mock_open.side_effect = urllib.error.URLError(reason="[Errno -2] Name or service not known")
        with self.assertRaises(_UpdateError) as ctx:
            _http_get_json("https://api.github.com/test")
        self.assertEqual(ctx.exception.code, "no_network")


# ─── display_check_update Output Tests ────────────────────────────────────────

class TestDisplayCheckUpdate(unittest.TestCase):

    def _run(self, local_version: str, mock_fn) -> str:
        """Captures stdout from display_check_update."""
        local = {"version": local_version, "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        captured = StringIO()
        with patch("sys.stdout", captured):
            with patch("urllib.request.urlopen", mock_fn):
                display_check_update(local)
        return captured.getvalue()

    @patch("urllib.request.urlopen")
    def test_update_available_shows_banner(self, mock_open):
        mock_open.return_value = _mock_urlopen(_make_release("v1.0.1"))
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            display_check_update(local)
        self.assertIn("UPDATE AVAILABLE", out.getvalue())
        self.assertIn("1.0.1", out.getvalue())

    @patch("urllib.request.urlopen")
    def test_no_update_shows_ok(self, mock_open):
        mock_open.return_value = _mock_urlopen(_make_release("v1.0.0"))
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            display_check_update(local)
        self.assertIn("latest version", out.getvalue())

    @patch("urllib.request.urlopen")
    def test_404_shows_friendly_message(self, mock_open):
        mock_open.side_effect = urllib.error.HTTPError(
            url="", code=404, msg="Not Found", hdrs={}, fp=None
        )
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            display_check_update(local)
        output = out.getvalue()
        self.assertNotIn("HTTP Error 404", output)
        self.assertNotIn("Traceback", output)
        self.assertIn("No published releases", output)

    @patch("urllib.request.urlopen")
    def test_rate_limit_shows_friendly_message(self, mock_open):
        mock_fp = MagicMock()
        mock_fp.read.return_value = b'{"message":"API rate limit exceeded"}'
        mock_open.side_effect = urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs={}, fp=mock_fp
        )
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            display_check_update(local)
        output = out.getvalue()
        self.assertNotIn("HTTP Error 403", output)
        self.assertNotIn("Traceback", output)
        self.assertIn("rate limit", output.lower())

    @patch("urllib.request.urlopen")
    def test_no_network_shows_friendly_message(self, mock_open):
        mock_open.side_effect = urllib.error.URLError(reason="[Errno 11001] getaddrinfo failed")
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            display_check_update(local)
        output = out.getvalue()
        self.assertNotIn("Traceback", output)
        self.assertIn("reach GitHub", output)

    @patch("urllib.request.urlopen")
    def test_timeout_shows_friendly_message(self, mock_open):
        mock_open.side_effect = urllib.error.URLError(reason="timed out")
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            display_check_update(local)
        output = out.getvalue()
        self.assertNotIn("Traceback", output)
        self.assertIn("GitHub", output)

    @patch("urllib.request.urlopen")
    def test_release_notes_are_displayed(self, mock_open):
        release = _make_release("v1.1.0", body="- New dashboard\n- Bug fixes")
        mock_open.return_value = _mock_urlopen(release)
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            display_check_update(local)
        output = out.getvalue()
        self.assertIn("New dashboard", output)
        self.assertIn("Bug fixes", output)


# ─── auto_check_on_start Tests ────────────────────────────────────────────────

class TestAutoCheckOnStart(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_shows_update_notification_if_newer(self, mock_open):
        mock_open.return_value = _mock_urlopen(_make_release("v2.0.0"))
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            auto_check_on_start(local, silent=True)
        self.assertIn("2.0.0", out.getvalue())

    @patch("urllib.request.urlopen")
    def test_silent_when_up_to_date(self, mock_open):
        mock_open.return_value = _mock_urlopen(_make_release("v1.0.0"))
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        out = StringIO()
        with patch("sys.stdout", out):
            auto_check_on_start(local, silent=True)
        self.assertEqual(out.getvalue().strip(), "")

    @patch("urllib.request.urlopen")
    def test_never_crashes_on_network_error(self, mock_open):
        mock_open.side_effect = urllib.error.URLError(reason="offline")
        local = {"version": "1.0.0", "channel": "stable", "build": "test", "release_date": "2026-07-06"}
        # Should not raise
        try:
            auto_check_on_start(local, silent=True)
        except Exception as e:
            self.fail(f"auto_check_on_start raised an exception: {e}")


# ─── get_local_version Tests ──────────────────────────────────────────────────

class TestGetLocalVersion(unittest.TestCase):

    def test_returns_dict_with_required_keys(self):
        result = get_local_version()
        self.assertIn("version", result)
        self.assertIn("channel", result)
        self.assertIn("build", result)
        self.assertIn("release_date", result)

    def test_version_is_string(self):
        result = get_local_version()
        self.assertIsInstance(result["version"], str)

    def test_version_is_not_empty(self):
        result = get_local_version()
        self.assertTrue(len(result["version"]) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
