# -*- coding: utf-8 -*-
"""
Unit Test Suite for DroidMaster Pro - Smart Device Profiles & Route Resolution
Covers:
- DeviceProfile data model serialization & deserialization
- DeviceManager profile persistence (add, update, delete, default POCO F1 initialization)
- Intelligent route resolution matrix (USB -> LAN -> Tailscale fallback)
- Scrcpy launch flags with no_audio & extra_args
- ProfileDialog GUI component initialization & field mapping
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Dynamic path resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from device_manager import DeviceProfile, DeviceManager, is_socket_reachable
import adb_core

# Ensure headless Qt application for GUI testing
from PySide6.QtWidgets import QApplication
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv + ["-platform", "offscreen"])

from profile_dialog import ProfileDialog


class TestDeviceProfileModel(unittest.TestCase):
    """Test DeviceProfile data model serialization, deserialization, and methods."""

    def test_profile_serialization_roundtrip(self):
        prof = DeviceProfile(
            id="poco_f1_test",
            name="📱 POCO F1 Test",
            model="POCOPHONE F1",
            usb_serial="9e29bf42",
            lan_endpoint="192.168.1.100:5555",
            tailscale_endpoint="100.83.144.79:5555",
            preferred_route="auto",
            extra_scrcpy_flags=["--no-audio", "--max-fps", "60"],
            auto_reconnect=True,
            max_reconnect_attempts=5,
            notes="Test unit profile",
        )

        d = prof.to_dict()
        self.assertEqual(d["id"], "poco_f1_test")
        self.assertEqual(d["name"], "📱 POCO F1 Test")
        self.assertEqual(d["usb_serial"], "9e29bf42")
        self.assertIn("--no-audio", d["extra_scrcpy_flags"])

        restored = DeviceProfile.from_dict(d)
        self.assertEqual(restored.id, prof.id)
        self.assertEqual(restored.name, prof.name)
        self.assertEqual(restored.lan_endpoint, prof.lan_endpoint)
        self.assertEqual(restored.tailscale_endpoint, prof.tailscale_endpoint)
        self.assertEqual(restored.extra_scrcpy_flags, ["--no-audio", "--max-fps", "60"])
        self.assertEqual(restored.max_reconnect_attempts, 5)

    def test_get_best_endpoint(self):
        # 1. Tailscale preferred
        p1 = DeviceProfile(id="p1", name="P1", preferred_route="tailscale", tailscale_endpoint="100.1.2.3:5555", lan_endpoint="192.168.1.2:5555")
        self.assertEqual(p1.get_best_endpoint(), "100.1.2.3:5555")

        # 2. LAN preferred
        p2 = DeviceProfile(id="p2", name="P2", preferred_route="lan", tailscale_endpoint="100.1.2.3:5555", lan_endpoint="192.168.1.2:5555")
        self.assertEqual(p2.get_best_endpoint(), "192.168.1.2:5555")

        # 3. Auto route fallback
        p3 = DeviceProfile(id="p3", name="P3", preferred_route="auto", tailscale_endpoint="100.1.2.3:5555")
        self.assertEqual(p3.get_best_endpoint(), "100.1.2.3:5555")


class TestDeviceManager(unittest.TestCase):
    """Test DeviceManager persistence and route resolution."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file.close()
        os.unlink(self.temp_file.name)
        self.manager = DeviceManager(storage_path=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except Exception:
                pass

    def test_default_profile_creation(self):
        """When storage file is empty or missing, manager should initialize default POCO F1 profile."""
        profs = self.manager.get_profiles()
        self.assertGreaterEqual(len(profs), 1)
        default_prof = profs[0]
        self.assertIn("POCO F1", default_prof.name)
        self.assertEqual(default_prof.tailscale_endpoint, "100.83.144.79:5555")
        self.assertIn("--no-audio", default_prof.extra_scrcpy_flags)

    def test_add_update_delete_profile(self):
        new_prof = DeviceProfile(
            id="samsung_s24",
            name="📱 Samsung S24 Office",
            model="SM-S928B",
            lan_endpoint="192.168.0.88:5555",
            tailscale_endpoint="100.90.1.2:5555",
        )
        self.manager.save_profile(new_prof)
        self.assertIsNotNone(self.manager.get_profile("samsung_s24"))

        # Re-instantiate from disk
        disk_manager = DeviceManager(storage_path=self.temp_file.name)
        loaded = disk_manager.get_profile("samsung_s24")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.model, "SM-S928B")

        # Delete
        self.assertTrue(self.manager.delete_profile("samsung_s24"))
        self.assertIsNone(self.manager.get_profile("samsung_s24"))

    def test_resolve_best_route_usb_priority(self):
        """When USB serial is present in connected list, route should resolve to USB."""
        prof = DeviceProfile(
            id="test_dev",
            name="Test Phone",
            usb_serial="9e29bf42",
            lan_endpoint="192.168.1.50:5555",
            tailscale_endpoint="100.83.144.79:5555",
            preferred_route="auto",
        )
        route_type, endpoint = self.manager.resolve_best_route(prof, connected_serials=["9e29bf42", "emulator-5554"])
        self.assertEqual(route_type, "USB")
        self.assertEqual(endpoint, "9e29bf42")

    def test_resolve_best_route_lan_fallback(self):
        """When USB not connected, but LAN socket is reachable, route resolves to LAN."""
        prof = DeviceProfile(
            id="test_dev",
            name="Test Phone",
            usb_serial="9e29bf42",
            lan_endpoint="192.168.1.50:5555",
            tailscale_endpoint="100.83.144.79:5555",
            preferred_route="auto",
        )
        with patch("device_manager.is_socket_reachable", return_value=True):
            route_type, endpoint = self.manager.resolve_best_route(prof, connected_serials=[])
        self.assertEqual(route_type, "LAN")
        self.assertEqual(endpoint, "192.168.1.50:5555")

    def test_resolve_best_route_tailscale_fallback(self):
        """When USB not connected and LAN socket unreachable, route falls back to Tailscale."""
        prof = DeviceProfile(
            id="test_dev",
            name="Test Phone",
            usb_serial="9e29bf42",
            lan_endpoint="192.168.1.50:5555",
            tailscale_endpoint="100.83.144.79:5555",
            preferred_route="auto",
        )
        with patch("device_manager.is_socket_reachable", return_value=False):
            route_type, endpoint = self.manager.resolve_best_route(prof, connected_serials=[])
        self.assertEqual(route_type, "Tailscale")
        self.assertEqual(endpoint, "100.83.144.79:5555")

    def test_resolve_explicit_tailscale_route(self):
        """When preferred_route is explicitly set to tailscale, it should always pick Tailscale."""
        prof = DeviceProfile(
            id="test_dev",
            name="Test Phone",
            usb_serial="9e29bf42",
            lan_endpoint="192.168.1.50:5555",
            tailscale_endpoint="100.83.144.79:5555",
            preferred_route="tailscale",
        )
        route_type, endpoint = self.manager.resolve_best_route(prof, connected_serials=["9e29bf42"])
        self.assertEqual(route_type, "Tailscale")
        self.assertEqual(endpoint, "100.83.144.79:5555")

    def test_resolve_best_route_mdns_discovery(self):
        """When USB is unplugged and LAN endpoint not set, mDNS auto-discovery should resolve dynamic port."""
        prof = DeviceProfile(
            id="test_lenovo",
            name="Tablet Lenovo",
            usb_serial="HA201ZLA",
            lan_endpoint="",
            tailscale_endpoint="100.79.177.114:5555",
            preferred_route="auto",
        )
        mock_services = [{
            "name": "adb-HA201ZLA-WnQTEc",
            "type": "_adb-tls-connect._tcp",
            "endpoint": "192.168.0.230:45485",
            "serial": "HA201ZLA"
        }]
        with patch("adb_core.discover_mdns_services", return_value=mock_services):
            route_type, endpoint = self.manager.resolve_best_route(prof, connected_serials=[])
        self.assertEqual(route_type, "Wi-Fi mDNS")
        self.assertEqual(endpoint, "192.168.0.230:45485")
        # Check that it auto-saved to profile.lan_endpoint
        self.assertEqual(prof.lan_endpoint, "192.168.0.230:45485")


class TestScrcpyLaunchWithProfileOptions(unittest.TestCase):
    """Test launch_scrcpy correctly appends profile flags (--no-audio, extra_args)."""

    @patch("adb_core.subprocess.Popen")
    @patch("adb_core.os.path.exists", return_value=True)
    def test_launch_scrcpy_with_no_audio(self, mock_exists, mock_popen):
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        opts = {
            "title": "DroidMaster Test",
            "no_audio": True,
            "extra_args": ["--no-audio", "--max-fps", "60"]
        }
        proc = adb_core.launch_scrcpy("100.83.144.79:5555", opts)
        self.assertIsNotNone(proc)

        called_cmd = mock_popen.call_args[0][0]
        self.assertIn("--no-audio", called_cmd)
        self.assertIn("--max-fps", called_cmd)
        self.assertIn("60", called_cmd)


class TestProfileDialogGUI(unittest.TestCase):
    """Verify ProfileDialog initializes cleanly and populates fields from profile."""

    def test_dialog_lifecycle(self):
        dlg = ProfileDialog()
        self.assertGreaterEqual(dlg.list_profiles.count(), 1)
        self.assertIsNotNone(dlg.current_profile)
        self.assertIn("POCO F1", dlg.txt_name.text())
        self.assertEqual(dlg.txt_tailscale.text(), "100.83.144.79:5555")
        self.assertTrue(dlg.chk_no_audio.isChecked())
        dlg.close()


if __name__ == "__main__":
    unittest.main()
