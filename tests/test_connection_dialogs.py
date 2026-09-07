# -*- coding: utf-8 -*-
"""
Tests for DroidMaster Pro Connection & Onboarding Dialogs
Verifies ConnectingProgressDialog, TailscaleOnboardingDialog, and should_show_tailscale_hint logic.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Ensure QApplication instance exists for GUI tests
app = QApplication.instance() or QApplication(sys.argv)

from device_manager import DeviceProfile
import adb_core
from connection_dialogs import (
    ConnectingProgressDialog,
    TailscaleOnboardingDialog,
    should_show_tailscale_hint,
)


class TestConnectionDialogs(unittest.TestCase):
    """Unit tests for connection dialogs and remote onboarding hint."""

    def setUp(self):
        self.profile = DeviceProfile(
            id="test-tablet",
            name="Tablet-Lenovo",
            usb_serial="1c8c5665",
            lan_endpoint="192.168.1.105",
            tailscale_endpoint="100.83.144.90",
            extra_scrcpy_flags=["--no-audio"]
        )

    def test_connecting_dialog_initial_state(self):
        """Verify dialog initializes with correct device name, zero progress and default UI."""
        dlg = ConnectingProgressDialog(profile=self.profile)
        self.assertEqual(dlg.lbl_device_name.text(), "📱 Tablet-Lenovo")
        self.assertEqual(dlg.progress_bar.value(), 0)
        self.assertIn("Connecting... 0%", dlg.lbl_percent.text())
        self.assertFalse(dlg.is_completed)
        self.assertFalse(dlg.is_error)
        dlg.close()

    def test_connecting_dialog_route_and_stage_updates(self):
        """Verify updating route badge and advancing through stages."""
        dlg = ConnectingProgressDialog(profile=self.profile)
        dlg.set_route_info("Tailscale", "100.83.144.90:5555")
        self.assertIn("Tailscale VPN", dlg.lbl_route_badge.text())
        self.assertIn("100.83.144.90:5555", dlg.lbl_route_badge.text())

        # Advance to stage 2
        dlg.update_stage(2, 55)
        self.assertEqual(dlg.target_progress, 55)
        self.assertIn("✓ 1.", dlg.step1_lbl.text())
        self.assertIn("⚡ 2.", dlg.step2_lbl.text())

        # Advance to stage 3
        dlg.update_stage(3, 85)
        self.assertEqual(dlg.target_progress, 85)
        self.assertIn("✓ 2.", dlg.step2_lbl.text())
        self.assertIn("🚀 3.", dlg.step3_lbl.text())

        dlg.close()

    def test_connecting_dialog_success_state(self):
        """Verify set_success reaches 100% and sets completed flag."""
        dlg = ConnectingProgressDialog(profile=self.profile)
        dlg.set_success("Kết nối thành công!")
        self.assertTrue(dlg.is_completed)
        self.assertEqual(dlg.progress_bar.value(), 100)
        self.assertIn("100%", dlg.lbl_percent.text())
        self.assertEqual(dlg.lbl_icon.text(), "✅")
        dlg.close()

    def test_connecting_dialog_error_state_and_retry(self):
        """Verify error state sets red UI and allows retry signal emission."""
        dlg = ConnectingProgressDialog(profile=self.profile)
        dlg.set_error("Không thể kết nối", "Timeout sau 5s", can_retry=True)
        self.assertTrue(dlg.is_error)
        self.assertEqual(dlg.lbl_icon.text(), "❌")
        self.assertFalse(dlg.error_frame.isHidden())
        self.assertFalse(dlg.btn_retry.isHidden())

        # Test retry click
        retry_called = []
        dlg.retry_requested.connect(lambda: retry_called.append(True))
        dlg.btn_retry.click()
        self.assertFalse(dlg.is_error)
        self.assertTrue(dlg.error_frame.isHidden())
        self.assertEqual(len(retry_called), 1)

        dlg.close()

    def test_connecting_dialog_cancel(self):
        """Verify clicking cancel emits cancelled signal."""
        dlg = ConnectingProgressDialog(profile=self.profile)
        cancelled = []
        dlg.cancelled.connect(lambda: cancelled.append(True))
        dlg.btn_cancel.click()
        self.assertEqual(len(cancelled), 1)

    def test_tailscale_onboarding_dialog_ui(self):
        """Verify onboarding dialog UI elements and texts."""
        dlg = TailscaleOnboardingDialog(device_name="Tablet-Lenovo", device_serial="1c8c5665")
        self.assertEqual(dlg.device_name, "Tablet-Lenovo")
        self.assertEqual(dlg.device_serial, "1c8c5665")
        self.assertTrue(dlg.chk_dont_show is not None)
        self.assertEqual(dlg.chk_dont_show.isChecked(), False)

        open_prof_called = []
        dlg.open_profiles_requested.connect(lambda: open_prof_called.append(True))
        dlg.btn_configure.click()
        self.assertEqual(len(open_prof_called), 1)
        dlg.close()

    @patch("adb_core.save_config")
    @patch("adb_core.load_config")
    def test_tailscale_onboarding_dialog_persist_dismissal(self, mock_load, mock_save):
        """Verify checking 'Do not show again' saves device serial to config.json."""
        mock_load.return_value = {"dismissed_tailscale_hints": []}
        dlg = TailscaleOnboardingDialog(device_name="Tablet-Lenovo", device_serial="1c8c5665")
        dlg.chk_dont_show.setChecked(True)
        dlg.btn_close.click()

        mock_save.assert_called_once()
        args = mock_save.call_args[0]
        self.assertEqual(args[0], "dismissed_tailscale_hints")
        self.assertIn("1c8c5665", args[1])

    @patch("adb_core.load_config")
    def test_should_show_tailscale_hint_logic(self, mock_load):
        """Verify rules determining when to show or hide the Tailscale onboarding popup."""
        mock_load.return_value = {"dismissed_tailscale_hints": ["dismissed-usb-123"]}

        # 1. Network endpoint (already wireless) -> False
        self.assertFalse(should_show_tailscale_hint("100.83.144.79:5555"))
        self.assertFalse(should_show_tailscale_hint("192.168.1.10:5555"))

        # 2. USB endpoint already dismissed -> False
        self.assertFalse(should_show_tailscale_hint("dismissed-usb-123"))

        # 3. Fresh USB endpoint without profile -> True
        self.assertTrue(should_show_tailscale_hint("fresh-usb-999"))

        # 4. Profile already has tailscale_endpoint filled -> False (don't nag configured devices)
        profile_configured = DeviceProfile(
            id="p1", name="P1", tailscale_endpoint="100.83.144.79:5555"
        )
        self.assertFalse(should_show_tailscale_hint("fresh-usb-999", profile=profile_configured))

        # 5. Profile has NO tailscale_endpoint -> True (prompt user to set it up!)
        profile_unconfigured = DeviceProfile(
            id="p2", name="P2", tailscale_endpoint=""
        )
        self.assertTrue(should_show_tailscale_hint("fresh-usb-999", profile=profile_unconfigured))


if __name__ == "__main__":
    unittest.main()
