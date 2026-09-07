# -*- coding: utf-8 -*-
"""
Unit Test Suite for DroidMaster ADB Core Engine and CyberDroid Automation
Covers:
- test_list_devices_parsing: USB, Wi-Fi, and edge cases (offline/empty/error).
- test_telemetry_batch_parsing: Multi-section batch output (PROP, BAT/BATTERY, WM, IP, WIN/APP, SU).
- test_text_escaping: ASCII escaping (%s, shell chars) and Unicode clipboard escaping/transliteration.
- test_ui_recon_xml_parsing: UIAutomator XML dump parsing (bounds, id, text, center coordinate, type).
- test_tap_text_auto_recon_retry: Automatic trigger of recon() when element not found in current cache.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Dynamically ensure both current dir, droid_master, and root scratch are in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

DROID_MASTER_DIR = os.path.join(PROJECT_DIR, "droid_master")
if os.path.isdir(DROID_MASTER_DIR) and DROID_MASTER_DIR not in sys.path:
    sys.path.insert(0, DROID_MASTER_DIR)

# Core imports
import adb_core
from adb_core import (
    list_devices,
    get_device_info,
    escape_text_for_adb,
    escape_text,
    escape_unicode_for_clipboard,
    escape_unicode_text,
    send_text,
    parse_ui_hierarchy,
    take_screenshot,
    take_screenshot_bytes,
    connect_wifi,
    switch_to_wifi,
    connect_endpoint,
    load_config,
    save_config,
    load_binary_manifest,
    verify_binary_manifest,
    DeviceOfflineError,
    ADBTimeoutError,
    ADBError,
)

import cyber_droid


class TestADBCore(unittest.TestCase):
    """Test suite for adb_core module functionality."""

    def test_list_devices_parsing(self):
        """Mock output of 'adb devices -l' for both USB and Wi-Fi devices,
        and verify parsed metadata dictionary.
        """
        mock_output = (
            "List of devices attached\n"
            "9e29bf42               device product:beryllium model:POCOPHONE_F1 device:beryllium transport_id:1\n"
            "192.168.0.106:5555     device product:beryllium model:POCOPHONE_F1 device:beryllium transport_id:2\n"
            "emulator-5554          offline product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 device:emu64a transport_id:3\n"
        )

        with patch("adb_core.run_adb_raw", return_value=(0, mock_output, "")):
            devices = list_devices()

        self.assertEqual(len(devices), 3)

        # 1. USB Connected Device
        usb_dev = devices[0]
        self.assertEqual(usb_dev["serial"], "9e29bf42")
        self.assertEqual(usb_dev["state"], "device")
        self.assertEqual(usb_dev["model"], "POCOPHONE F1")
        self.assertEqual(usb_dev["product"], "beryllium")
        self.assertEqual(usb_dev["type"], "USB")
        self.assertIn("POCOPHONE F1", usb_dev["display"])
        self.assertIn("[9e29bf42]", usb_dev["display"])
        self.assertIn("(USB)", usb_dev["display"])

        # 2. Wi-Fi Connected Device
        wifi_dev = devices[1]
        self.assertEqual(wifi_dev["serial"], "192.168.0.106:5555")
        self.assertEqual(wifi_dev["state"], "device")
        self.assertEqual(wifi_dev["model"], "POCOPHONE F1")
        self.assertEqual(wifi_dev["product"], "beryllium")
        self.assertEqual(wifi_dev["type"], "Wi-Fi")
        self.assertIn("POCOPHONE F1", wifi_dev["display"])
        self.assertIn("[192.168.0.106:5555]", wifi_dev["display"])
        self.assertIn("(Wi-Fi)", wifi_dev["display"])

        # 3. Offline Device
        offline_dev = devices[2]
        self.assertEqual(offline_dev["serial"], "emulator-5554")
        self.assertEqual(offline_dev["state"], "offline")
        self.assertEqual(offline_dev["type"], "USB")

        # 4. Edge Cases: empty device list and error exit code
        with patch("adb_core.run_adb_raw", return_value=(0, "List of devices attached\n\n", "")):
            self.assertEqual(list_devices(), [])

        with patch("adb_core.run_adb_raw", return_value=(1, "", "adb server failed to start")):
            self.assertEqual(list_devices(), [])

    def test_telemetry_batch_parsing(self):
        """Mock output of batch script with ===PROP===, ===BATTERY=== (or ===BAT===),
        ===WM===, ===IP===, ===WIN===, ===SU=== and verify parsing of battery, temp, ip, app, etc.
        """
        # Case A: Standard POCOPHONE F1 Telemetry Batch Output
        mock_batch_stdout = (
            "===PROP===\n"
            "POCOPHONE F1\n"
            "Xiaomi\n"
            "10\n"
            "29\n"
            "===BATTERY===\n"
            "Current Battery Service state:\n"
            "  level: 85\n"
            "  scale: 100\n"
            "  temperature: 365\n"
            "  technology: Li-poly\n"
            "===WM===\n"
            "Physical size: 1080x2246\n"
            "===IP===\n"
            "192.168.0.0/24 dev wlan0 proto kernel scope link src 192.168.0.106\n"
            "===WIN===\n"
            "  mCurrentFocus=Window{460a5d4 u0 com.android.settings/com.android.settings.SubSettings}\n"
            "===SU===\n"
            "/system/xbin/su\n"
        )

        with patch("adb_core.run_adb_raw", return_value=(0, mock_batch_stdout, "")):
            info = get_device_info("9e29bf42")

        self.assertEqual(info["model"], "POCOPHONE F1")
        self.assertEqual(info["brand"], "Xiaomi")
        self.assertEqual(info["android_version"], "Android 10 (SDK 29)")
        self.assertEqual(info["sdk"], "29")
        self.assertEqual(info["battery_level"], "85%")
        self.assertEqual(info["battery_temp"], "36.5°C")
        self.assertEqual(info["resolution"], "1080x2246")
        self.assertEqual(info["ip"], "192.168.0.106")
        self.assertEqual(info["active_app"], "com.android.settings")
        self.assertEqual(info["root"], "Đã phát hiện su binary")

        # Case B: Alternate syntax (===BAT===, ===WINDOW===, direct IP, unrooted)
        mock_alt_stdout = (
            "===PROP===\n"
            "Pixel 7\n"
            "google\n"
            "14\n"
            "34\n"
            "===BAT===\n"
            "level: 92\n"
            "temperature: 280\n"
            "===WM===\n"
            "Override size: 1080x2400\n"
            "===IP===\n"
            "10.0.0.155\n"
            "===WINDOW===\n"
            "mFocusedApp=AppWindowToken{435f21 u0 com.google.android.youtube/com.google.android.apps.youtube.app.WatchWhileActivity}\n"
            "===SU===\n"
            "su: not found\n"
        )

        with patch("adb_core.run_adb_raw", return_value=(0, mock_alt_stdout, "")):
            info_alt = get_device_info("pixel_serial")

        self.assertEqual(info_alt["model"], "Pixel 7")
        self.assertEqual(info_alt["brand"], "Google")
        self.assertEqual(info_alt["battery_level"], "92%")
        self.assertEqual(info_alt["battery_temp"], "28.0°C")
        self.assertEqual(info_alt["resolution"], "1080x2400")
        self.assertEqual(info_alt["ip"], "10.0.0.155")
        self.assertEqual(info_alt["active_app"], "com.google.android.youtube")
        self.assertEqual(info_alt["root"], "Không có (Chưa root)")

    def test_text_escaping(self):
        """Test escaping functions for both ASCII and Unicode / Vietnamese characters."""
        # 1. ASCII Text Escaping for adb shell input text
        raw_ascii = 'Hello World & <tag> > "double" \'single\''
        escaped_ascii = escape_text_for_adb(raw_ascii)
        self.assertNotIn(" ", escaped_ascii)
        self.assertIn("%s", escaped_ascii)
        self.assertIn("\\&", escaped_ascii)
        self.assertIn("\\<", escaped_ascii)
        self.assertIn("\\>", escaped_ascii)
        self.assertIn('\\"', escaped_ascii)
        self.assertIn("\\'", escaped_ascii)

        # Alias check
        self.assertEqual(escape_text(raw_ascii), escaped_ascii)

        # Empty string check
        self.assertEqual(escape_text_for_adb(""), "")

        # 2. Unicode / Vietnamese Shell Clipboard Escaping
        unicode_str = "Xin chào Việt Nam! 🇻🇳 Special & symbols"
        escaped_uni = escape_unicode_for_clipboard(unicode_str)
        self.assertTrue(escaped_uni.startswith("'") and escaped_uni.endswith("'"))
        self.assertIn("Xin chào Việt Nam!", escaped_uni)

        # Alias check
        self.assertEqual(escape_unicode_text(unicode_str), escaped_uni)

        # 3. send_text integration with Android 13+ clipboard execution
        with patch("adb_core.run_adb_raw") as mock_run:
            mock_run.return_value = (0, "", "")
            code, out, err = send_text("mock_serial", "Cài đặt hệ thống")
            self.assertEqual(code, 0)
            # Verify clipboard set was called with quoted text
            mock_run.assert_any_call(["shell", f"cmd clipboard set {escape_unicode_for_clipboard('Cài đặt hệ thống')}"], serial="mock_serial")
            # Verify paste keyevent 279 was injected
            mock_run.assert_any_call(["shell", "input", "keyevent", "279"], serial="mock_serial")

        # 4. send_text fallback when cmd clipboard is unsupported
        with patch("adb_core.run_adb_raw") as mock_run:
            # First call (clipboard) returns failure; second call (input text) returns success
            mock_run.side_effect = [
                (1, "", "No shell command implementation"),
                (0, "", "")
            ]
            code, out, err = send_text("mock_serial", "Xin chào")
            self.assertEqual(code, 0)
            # Fallback transliterates 'Xin chào' -> 'Xin chao' and escapes spaces
            mock_run.assert_any_call(["shell", "input", "text", "Xin%schao"], serial="mock_serial")

    def test_ui_recon_xml_parsing(self):
        """Mock UIAutomator dump XML tree and verify extraction of bounds,
        id, short_id, text, center coordinate, and interactive types.
        """
        mock_xml = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.settings" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,0][1080,2246]">
    <node index="0" text="Settings" resource-id="com.android.settings:id/homepage_title" class="android.widget.TextView" package="com.android.settings" content-desc="Settings Title" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[50,120][450,220]" />
    <node index="1" text="Search settings" resource-id="com.android.settings:id/search_action_bar" class="android.widget.Button" package="com.android.settings" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[60,240][1020,360]" />
    <node index="2" text="" resource-id="com.android.settings:id/back_arrow" class="android.widget.ImageButton" package="com.android.settings" content-desc="Navigate up" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[30,50][150,170]" />
    <node index="3" text="Network &amp; internet" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[200,400][900,480]" />
  </node>
</hierarchy>
"""
        elements = parse_ui_hierarchy(mock_xml)
        self.assertEqual(len(elements), 4)

        # 1. Element 0: Homepage Title
        elem0 = elements[0]
        self.assertEqual(elem0["text"], "Settings")
        self.assertEqual(elem0["desc"], "Settings Title")
        self.assertEqual(elem0["resource_id"], "com.android.settings:id/homepage_title")
        self.assertEqual(elem0["short_id"], "homepage_title")
        self.assertEqual(elem0["bounds"], "[50,120][450,220]")
        self.assertEqual(elem0["coords"], (50, 120, 450, 220))
        # Center = ((50 + 450) // 2, (120 + 220) // 2) = (250, 170)
        self.assertEqual(elem0["center"], (250, 170))
        self.assertEqual(elem0["type"], "TextView")
        self.assertTrue(elem0["clickable"])

        # 2. Element 1: Search Button
        elem1 = elements[1]
        self.assertEqual(elem1["text"], "Search settings")
        self.assertEqual(elem1["resource_id"], "com.android.settings:id/search_action_bar")
        self.assertEqual(elem1["short_id"], "search_action_bar")
        self.assertEqual(elem1["bounds"], "[60,240][1020,360]")
        self.assertEqual(elem1["coords"], (60, 240, 1020, 360))
        # Center = ((60 + 1020) // 2, (240 + 360) // 2) = (540, 300)
        self.assertEqual(elem1["center"], (540, 300))
        self.assertEqual(elem1["type"], "Button")

        # 3. Element 2: Icon button with content-desc
        elem2 = elements[2]
        self.assertEqual(elem2["text"], "")
        self.assertEqual(elem2["desc"], "Navigate up")
        self.assertEqual(elem2["short_id"], "back_arrow")
        # Center = ((30 + 150) // 2, (50 + 170) // 2) = (90, 110)
        self.assertEqual(elem2["center"], (90, 110))
        self.assertEqual(elem2["type"], "ImageButton")

        # 4. Element 3: Text node with XML entities (&amp;)
        elem3 = elements[3]
        self.assertEqual(elem3["text"], "Network & internet")
        self.assertEqual(elem3["short_id"], "title")
        # Center = ((200 + 900) // 2, (400 + 480) // 2) = (550, 440)
        self.assertEqual(elem3["center"], (550, 440))

    def test_telemetry_cpu_parsing(self):
        """Mock output containing ===CPU=== TOTAL: 14.5%... and verify
        that info['cpu'] is correctly parsed.
        """
        # Case 1: Standard dumpsys cpuinfo format with TOTAL: 14.5%
        mock_cpu_stdout = (
            "===BATTERY===\nlevel: 80\n"
            "===IP===\n192.168.1.50\n"
            "===WIN===\nmCurrentFocus=Window{123 u0 com.android.settings}\n"
            "===CPU===\n"
            "Load: 2.1 / 1.8 / 1.2\n"
            "TOTAL: 14.5% (user 9.2% + kernel 5.3% + iowait 0% + softirq 0%)\n"
        )
        with patch("adb_core.run_adb_raw", return_value=(0, mock_cpu_stdout, "")):
            info = get_device_info("test_serial_cpu", dynamic_only=True)
        self.assertEqual(info["cpu"], "14.5%")

        # Case 2: Alternate format "14.5% TOTAL"
        mock_alt_cpu = (
            "===CPU===\n"
            "14.5% TOTAL: 10% user + 4.5% kernel\n"
        )
        with patch("adb_core.run_adb_raw", return_value=(0, mock_alt_cpu, "")):
            info_alt = get_device_info("test_serial_cpu_alt", dynamic_only=True)
        self.assertEqual(info_alt["cpu"], "14.5%")

        # Case 3: Empty CPU output defaults gracefully
        with patch("adb_core.run_adb_raw", return_value=(0, "===BATTERY===\nlevel: 80\n", "")):
            info_empty = get_device_info("test_serial_cpu_empty", dynamic_only=True)
        self.assertEqual(info_empty["cpu"], "--%")

        # Case 4: Prompt format '12% TOTAL'
        mock_prompt_cpu = (
            "===CPU===\n"
            "12% TOTAL\n"
        )
        with patch("adb_core.run_adb_raw", return_value=(0, mock_prompt_cpu, "")):
            info_p = get_device_info("test_serial_prompt_cpu", dynamic_only=True)
        self.assertEqual(info_p["cpu"], "12%")

    def test_take_screenshot_bytes(self):
        """Mock exec-out screencap returning bytes b'\\x89PNG\\r\\n\\x1a\\n...' and
        verify that take_screenshot_bytes returns the valid bytes.
        """
        mock_png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x04\x38\x00\x00\x07\x80'
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = mock_png_bytes

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            raw_bytes = take_screenshot_bytes("mock_serial")
            self.assertIsNotNone(raw_bytes)
            self.assertTrue(raw_bytes.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(raw_bytes, mock_png_bytes)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("exec-out", args)
            self.assertIn("screencap", args)
            self.assertIn("-p", args)

        # Test failure case: returncode != 0
        mock_proc_fail = MagicMock()
        mock_proc_fail.returncode = 1
        mock_proc_fail.stdout = b'Error capturing screen'
        with patch("subprocess.run", return_value=mock_proc_fail):
            res = take_screenshot_bytes("mock_serial")
            self.assertIn(res, (None, b""))

        # Test failure case: corrupted / non-PNG output
        mock_proc_corrupt = MagicMock()
        mock_proc_corrupt.returncode = 0
        mock_proc_corrupt.stdout = b'Corrupted bytes'
        with patch("subprocess.run", return_value=mock_proc_corrupt):
            res = take_screenshot_bytes("mock_serial")
            self.assertIn(res, (None, b""))

    def test_binary_manifest_validation(self):
        """Read bin/manifest.json (if present) and verify json structure contains
        adb.exe, scrcpy.exe, scrcpy-server and 64-character SHA-256 hashes.
        """
        bin_dir = adb_core.BIN_DIR or os.path.join(PROJECT_DIR, "bin")
        manifest_file = os.path.join(bin_dir, "manifest.json")

        manifest = load_binary_manifest(manifest_file)
        self.assertTrue(bool(manifest), f"Manifest file should exist at {manifest_file} and not be empty")

        # Extract file map (supports 'files' key, 'binaries' key, or root dict)
        file_entries = manifest.get("files") or manifest.get("binaries") or manifest

        required_binaries = ["adb.exe", "scrcpy.exe", "scrcpy-server"]
        hex_chars = set("0123456789abcdefABCDEF")

        for bin_name in required_binaries:
            self.assertIn(bin_name, file_entries, f"Manifest must contain entry for {bin_name}")
            entry = file_entries[bin_name]
            sha = entry["sha256"] if isinstance(entry, dict) else entry
            self.assertIsInstance(sha, str)
            self.assertEqual(len(sha), 64, f"SHA-256 for {bin_name} must be exactly 64 hex characters")
            self.assertTrue(all(c in hex_chars for c in sha), f"SHA-256 for {bin_name} contains invalid hex characters")

        # Verify against actual files if present
        import hashlib
        for bin_name in required_binaries:
            bin_path = os.path.join(bin_dir, bin_name)
            if os.path.isfile(bin_path):
                hasher = hashlib.sha256()
                with open(bin_path, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                computed_sha = hasher.hexdigest().lower()
                entry = file_entries[bin_name]
                expected_sha = (entry["sha256"] if isinstance(entry, dict) else entry).lower()
                self.assertEqual(computed_sha, expected_sha, f"Physical binary {bin_name} SHA-256 mismatch")

    def test_wifi_tcpip_failure(self):
        """Mock when tcpip command returns exit code != 0.
        Verify connect_wifi returns controlled failure (ok=False) or raises exception when check=True.
        """
        # Case 1: Controlled failure (ok=False, message string)
        with patch("adb_core.run_adb_raw", return_value=(1, "", "error: closed")):
            ok, msg = connect_wifi("mock_device", "192.168.1.100", 5555)
            self.assertFalse(ok)
            self.assertIn("error: closed", msg)

        # Case 2: Controlled failure when adb device is unauthorized/offline
        with patch("adb_core.run_adb_raw", return_value=(1, "", "error: device unauthorized")):
            ok, msg = connect_wifi("mock_device", "192.168.1.100", 5555)
            self.assertFalse(ok)
            self.assertIn("device unauthorized", msg)

        # Case 3: When check=True, raises ADBError
        with patch("adb_core.run_adb_raw", return_value=(1, "", "error: tcpip failed")):
            with self.assertRaises(ADBError) as ctx:
                connect_wifi("mock_device", "192.168.1.100", 5555, check=True)
            self.assertEqual(ctx.exception.returncode, 1)

    def test_take_screenshot_with_output_path(self):
        """Verify take_screenshot saves bytes to output_path and returns raw bytes."""
        import tempfile
        mock_png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        with patch("adb_core.take_screenshot_bytes", return_value=mock_png_bytes):
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_file = os.path.join(tmp_dir, "test_snap.png")
                ret_bytes = take_screenshot("mock_serial", out_file)
                self.assertEqual(ret_bytes, mock_png_bytes)
                self.assertTrue(os.path.isfile(out_file))
                with open(out_file, "rb") as f:
                    self.assertEqual(f.read(), mock_png_bytes)

    def test_connect_wifi_success(self):
        """Test successful connect_wifi execution with return code and stdout checks."""
        with patch("adb_core.run_adb_raw") as mock_run:
            mock_run.side_effect = [
                (0, "restarting in TCP mode port: 5555", ""),
                (0, "connected to 192.168.1.100:5555", ""),
            ]
            ok, msg = connect_wifi("mock_device", "192.168.1.100", 5555)
            self.assertTrue(ok)
            self.assertIn("192.168.1.100:5555", msg)

    def test_connect_wifi_auto_ip(self):
        """Test connect_wifi with auto-discovered IP from get_device_info."""
        with patch("adb_core.run_adb_raw") as mock_run, \
             patch("adb_core.get_device_info", return_value={"ip": "10.0.0.5"}):
            mock_run.side_effect = [
                (0, "restarting in TCP mode port: 5555", ""),
                (0, "connected to 10.0.0.5:5555", ""),
            ]
            ok, msg = connect_wifi("mock_device", port=5555)
            self.assertTrue(ok)
            self.assertIn("10.0.0.5:5555", msg)

    def test_connect_wifi_already_connected(self):
        """Test connect_wifi and switch_to_wifi when device reports already connected."""
        with patch("adb_core.run_adb_raw") as mock_run:
            mock_run.side_effect = [
                (0, "restarting in TCP mode port: 5555", ""),
                (0, "already connected to 192.168.1.100:5555", ""),
            ]
            ok, msg = switch_to_wifi("mock_device", "192.168.1.100", 5555)
            self.assertTrue(ok)
            self.assertIn("192.168.1.100:5555", msg)

    def test_connect_endpoint_direct(self):
        """Test connect_endpoint connects directly to IP or IP:port without requiring USB."""
        with patch("adb_core.run_adb_raw", return_value=(0, "connected to 192.168.0.50:5555", "")):
            ok, msg = connect_endpoint("192.168.0.50")
            self.assertTrue(ok)
            self.assertIn("192.168.0.50:5555", msg)

        # Test failure
        with patch("adb_core.run_adb_raw", return_value=(1, "", "cannot connect to 192.168.0.50:5555")):
            ok, msg = connect_endpoint("192.168.0.50")
            self.assertFalse(ok)
            self.assertIn("cannot connect", msg)

    def test_config_persistence(self):
        """Test load_config and save_config functionality."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_cfg_path = os.path.join(tmp_dir, "test_config.json")
            with patch("adb_core.CONFIG_PATH", test_cfg_path):
                save_config("last_wifi_endpoint", "10.0.0.99:5555")
                cfg = load_config()
                self.assertEqual(cfg.get("last_wifi_endpoint"), "10.0.0.99:5555")

    def test_verify_binary_manifest_real_and_mock(self):
        """Test verify_binary_manifest on actual bin/manifest.json and edge cases."""
        import tempfile
        import json

        # 1. Real manifest check
        res = verify_binary_manifest()
        self.assertTrue(res["manifest_found"])
        self.assertTrue(res["valid"])
        self.assertGreater(res["checked_count"], 0)
        self.assertEqual(len(res["errors"]), 0)

        # 2. Missing manifest check
        res_missing = verify_binary_manifest("/non/existent/manifest.json")
        self.assertFalse(res_missing["manifest_found"])
        self.assertFalse(res_missing["valid"])

        # 3. Hash mismatch check
        with tempfile.TemporaryDirectory() as tmp_dir:
            dummy_file = os.path.join(tmp_dir, "fake.bin")
            with open(dummy_file, "wb") as f:
                f.write(b"content")
            manifest_file = os.path.join(tmp_dir, "manifest.json")
            with open(manifest_file, "w") as f:
                json.dump({"files": {"fake.bin": "0" * 64}}, f)

            res_mismatch = verify_binary_manifest(manifest_file)
            self.assertTrue(res_mismatch["manifest_found"])
            self.assertFalse(res_mismatch["valid"])
            self.assertEqual(res_mismatch["files"]["fake.bin"]["status"], "mismatch")

    def test_launch_scrcpy_smart_fallback(self):
        """Test that launch_scrcpy automatically falls back to an active Wi-Fi device
        if the target USB serial was unplugged.
        """
        from unittest.mock import patch, MagicMock

        # Mock list_devices returning only the active Wi-Fi device
        mock_devices = [
            {"serial": "192.168.0.106:5555", "state": "device", "model": "POCOPHONE F1", "type": "Wi-Fi"}
        ]
        with patch("adb_core.os.path.exists", return_value=True):
            with patch("adb_core.list_devices", return_value=mock_devices):
                with patch("subprocess.Popen") as mock_popen:
                    mock_proc = MagicMock()
                    mock_popen.return_value = mock_proc

                    # Requesting old USB serial '96469ba4' which is now gone
                    proc = adb_core.launch_scrcpy("96469ba4", {"always_on_top": True})
                    self.assertIsNotNone(proc)

                    # Verify scrcpy was called with the fallback Wi-Fi serial!
                    called_cmd = mock_popen.call_args[0][0]
                    self.assertIn("-s", called_cmd)
                    serial_idx = called_cmd.index("-s") + 1
                    self.assertEqual(called_cmd[serial_idx], "192.168.0.106:5555")


class TestCyberDroid(unittest.TestCase):
    """Test suite for cyber_droid automation improvements."""

    def test_tap_text_auto_recon_retry(self):
        """Test that tap_text / cmd_tap_text automatically triggers recon()
        to refresh the UI hierarchy when the element is not found in the initial cache.
        """
        # Initial state: cache only contains an unrelated 'Home' element
        initial_cache = [
            {
                "type": "Button",
                "text": "Home",
                "desc": "",
                "resource_id": "com.android.launcher:id/home",
                "short_id": "home",
                "bounds": "[100,100][200,200]",
                "coords": (100, 100, 200, 200),
                "center": (150, 150),
                "clickable": True
            }
        ]
        cyber_droid.RECON_ELEMENTS = list(initial_cache)

        # Refreshed state after recon(): now includes 'Settings' element
        refreshed_cache = list(initial_cache) + [
            {
                "type": "TextView",
                "text": "Settings",
                "desc": "",
                "resource_id": "com.android.settings:id/title",
                "short_id": "title",
                "bounds": "[300,500][700,600]",
                "coords": (300, 500, 700, 600),
                "center": (500, 550),
                "clickable": True
            }
        ]

        recon_called = False

        def mock_cmd_recon(serial=None):
            nonlocal recon_called
            recon_called = True
            cyber_droid.RECON_ELEMENTS = list(refreshed_cache)

        with patch.object(cyber_droid, "cmd_recon", side_effect=mock_cmd_recon):
            with patch.object(cyber_droid, "run_adb_raw", return_value=(0, "", "")) as mock_adb:
                success = cyber_droid.cmd_tap_text("Settings", serial="test_device")

                self.assertTrue(success)
                self.assertTrue(recon_called, "cmd_recon should have been triggered automatically!")
                # Verify that adb input tap was dispatched to (500, 550)
                mock_adb.assert_called_with(["shell", "input", "tap", "500", "550"], serial="test_device")

    def test_tap_text_not_found_even_after_recon(self):
        """Test that tap_text returns False and does not crash when the element
        is still absent after recon refresh.
        """
        cyber_droid.RECON_ELEMENTS = []

        def mock_cmd_recon_empty(serial=None):
            cyber_droid.RECON_ELEMENTS = []

        with patch.object(cyber_droid, "cmd_recon", side_effect=mock_cmd_recon_empty):
            success = cyber_droid.cmd_tap_text("NonExistentButton", serial="test_device")
            self.assertFalse(success)


class TestGuideDialog(unittest.TestCase):
    """Unit tests for the integrated in-app user guide."""

    def test_guide_html_anchors_and_content(self):
        import guide_dialog
        html = guide_dialog.GUIDE_HTML

        expected_anchors = [
            "sec_quickstart",
            "sec_xiaomi",
            "sec_samsung",
            "sec_oppo",
            "sec_vivo",
            "sec_pixel",
            "sec_huawei",
            "sec_wifi",
            "sec_stream",
            "sec_features",
            "sec_faq",
        ]
        for anchor in expected_anchors:
            self.assertIn(f'name="{anchor}"', html, f"Anchor {anchor} missing in GUIDE_HTML!")

        # Check critical troubleshooting & brand instructions
        self.assertIn("Xiaomi", html)
        self.assertIn("POCO", html)
        self.assertIn("HyperOS", html)
        self.assertIn("Samsung", html)
        self.assertIn("One UI", html)
        self.assertIn("Alt + Shift + O", html)
        self.assertIn("5555", html)
        self.assertIn("Tailscale", html)

    def test_guide_dialog_instantiation(self):
        from PySide6.QtWidgets import QApplication
        import guide_dialog

        app = QApplication.instance() or QApplication(sys.argv)
        dialog = guide_dialog.UserGuideDialog()
        self.assertIsNotNone(dialog)
        self.assertEqual(len(dialog.sections_map), 11)
        self.assertEqual(dialog.toc_list.count(), 11)
        dialog.close()


if __name__ == "__main__":
    unittest.main()