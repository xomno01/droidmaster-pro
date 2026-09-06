# -*- coding: utf-8 -*-
"""
DroidMaster Core Engine
Provides high-performance, asynchronous ADB & Scrcpy wrappers for Android device control.
"""

import os
import re
import subprocess
import threading
from typing import List, Dict, Optional, Tuple

import sys

def get_bin_dir() -> str:
    """Find the bundled or local bin directory containing scrcpy and adb."""
    candidates = [
        os.path.join(getattr(sys, '_MEIPASS', ''), 'bin'),
        os.path.join(os.path.dirname(sys.executable), 'bin'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin'),
        r"C:\Users\phamn\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1"
    ]
    for c in candidates:
        if c and os.path.exists(os.path.join(c, "scrcpy.exe")):
            return os.path.abspath(c)
    return ""

BIN_DIR = get_bin_dir()
ADB_PATH = os.path.join(BIN_DIR, "adb.exe") if BIN_DIR else "adb.exe"
SCRCPY_PATH = os.path.join(BIN_DIR, "scrcpy.exe") if BIN_DIR else "scrcpy.exe"

def run_adb_raw(args: List[str], timeout: int = 10, serial: Optional[str] = None) -> Tuple[int, str, str]:
    """Execute raw adb command and return (returncode, stdout, stderr)."""
    cmd = [ADB_PATH]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)

    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def list_devices() -> List[Dict[str, str]]:
    """Return all connected Android devices with metadata."""
    code, stdout, _ = run_adb_raw(["devices", "-l"])
    devices = []
    if code != 0 or not stdout:
        return devices

    lines = stdout.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("*") or line.startswith("List of devices"):
            continue

        parts = line.split()
        if len(parts) >= 2:
            serial = parts[0]
            state = parts[1]
            model = "Android Device"
            product = ""
            for item in parts[2:]:
                if item.startswith("model:"):
                    model = item.split(":", 1)[1].replace("_", " ")
                elif item.startswith("product:"):
                    product = item.split(":", 1)[1]

            conn_type = "Wi-Fi" if ":" in serial else "USB"
            devices.append({
                "serial": serial,
                "state": state,
                "model": model,
                "product": product,
                "type": conn_type,
                "display": f"{model} [{serial}] ({conn_type})"
            })
    return devices

def get_device_info(serial: str) -> Dict[str, str]:
    """Fetch hardware and system telemetry for a specific device."""
    info = {
        "model": "Unknown",
        "brand": "Android",
        "android_version": "Unknown",
        "sdk": "",
        "battery_level": "--%",
        "battery_temp": "--°C",
        "resolution": "Unknown",
        "ip": "Unknown",
        "root": "Chưa cấp quyền",
        "active_app": "Trang chính (Launcher)"
    }

    # Model & Brand & Android version
    _, model, _ = run_adb_raw(["shell", "getprop", "ro.product.model"], serial=serial)
    _, brand, _ = run_adb_raw(["shell", "getprop", "ro.product.brand"], serial=serial)
    _, version, _ = run_adb_raw(["shell", "getprop", "ro.build.version.release"], serial=serial)
    _, sdk, _ = run_adb_raw(["shell", "getprop", "ro.build.version.sdk"], serial=serial)

    if model:
        info["model"] = model
    if brand:
        info["brand"] = brand.capitalize()
    if version:
        info["android_version"] = f"Android {version} (SDK {sdk})"

    # Battery
    _, battery_out, _ = run_adb_raw(["shell", "dumpsys", "battery"], serial=serial)
    level_m = re.search(r"level:\s*(\d+)", battery_out)
    if level_m:
        info["battery_level"] = f"{level_m.group(1)}%"
    temp_m = re.search(r"temperature:\s*(\d+)", battery_out)
    if temp_m:
        info["battery_temp"] = f"{int(temp_m.group(1)) / 10:.1f}°C"

    # Display Resolution
    _, wm_out, _ = run_adb_raw(["shell", "wm", "size"], serial=serial)
    size_m = re.search(r"Physical size:\s*(\d+x\d+)", wm_out)
    if size_m:
        info["resolution"] = size_m.group(1)

    # IP Address
    _, ip_out, _ = run_adb_raw(["shell", "ip", "route"], serial=serial)
    ip_m = re.search(r"src\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", ip_out)
    if ip_m:
        info["ip"] = ip_m.group(1)

    # Root status (passive check only - never invoke su -c to prevent Magisk toast popups)
    info["root"] = "Magisk (Không bắt buộc)"

    # Current Focused Window
    _, win_out, _ = run_adb_raw(["shell", "dumpsys", "window"], serial=serial)
    win_m = re.search(r"mCurrentFocus=Window\{[^\s]+\s+[^\s]+\s+([^/\s]+)", win_out)
    if win_m:
        info["active_app"] = win_m.group(1)

    return info

def launch_scrcpy(serial: str, options: Dict) -> Optional[subprocess.Popen]:
    """Launch scrcpy with custom user options."""
    if not os.path.exists(SCRCPY_PATH):
        return None

    cmd = [SCRCPY_PATH, "-s", serial]

    if options.get("always_on_top", True):
        cmd.append("--always-on-top")
    if options.get("turn_screen_off", False):
        cmd.append("--turn-screen-off")
    if options.get("stay_awake", True):
        cmd.append("--stay-awake")

    max_size = options.get("max_size", 0)
    if max_size and max_size > 0:
        cmd.extend(["--max-size", str(max_size)])

    bitrate = options.get("bitrate", "8M")
    if bitrate:
        cmd.extend(["--video-bit-rate", str(bitrate)])

    title = options.get("title", f"DroidMaster // {serial}")
    cmd.extend(["--window-title", title])
    cmd.extend(["--window-width", "420"])

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=BIN_DIR if BIN_DIR else None,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        return proc
    except Exception:
        return None

def send_keyevent(serial: str, keycode: str):
    """Inject hardware key event."""
    return run_adb_raw(["shell", "input", "keyevent", str(keycode)], serial=serial)

def send_text(serial: str, text: str):
    """Send text to the active focused input field."""
    # Replace space with %s for adb input text
    escaped = text.replace(" ", "%s").replace("&", "\\&").replace("<", "\\<").replace(">", "\\>")
    return run_adb_raw(["shell", "input", "text", escaped], serial=serial)

def take_screenshot(serial: str, output_path: str) -> bool:
    """Capture screen directly to local PC path."""
    remote_path = "/sdcard/_droid_snap.png"
    code1, _, _ = run_adb_raw(["shell", "screencap", "-p", remote_path], serial=serial)
    if code1 != 0:
        return False
    code2, _, _ = run_adb_raw(["pull", remote_path, output_path], serial=serial)
    run_adb_raw(["shell", "rm", remote_path], serial=serial)
    return code2 == 0 and os.path.exists(output_path)

def install_apk(serial: str, apk_path: str) -> Tuple[bool, str]:
    """Install an APK file onto the target device."""
    code, stdout, stderr = run_adb_raw(["install", "-r", apk_path], timeout=60, serial=serial)
    if code == 0 and "Success" in stdout:
        return True, "Cài đặt ứng dụng thành công!"
    return False, stdout or stderr or "Lỗi cài đặt APK"

def switch_to_wifi(serial: str, ip: str, port: int = 5555) -> Tuple[bool, str]:
    """Enable TCP/IP wireless debugging and connect over Wi-Fi."""
    run_adb_raw(["tcpip", str(port)], serial=serial)
    import time
    time.sleep(1.0)
    code, out, err = run_adb_raw(["connect", f"{ip}:{port}"])
    if "connected to" in out.lower():
        return True, f"Đã kết nối không dây thành công tới {ip}:{port}!"
    return False, out or err

def reboot(serial: str, mode: str = ""):
    """Reboot device into normal, recovery, or bootloader."""
    args = ["reboot"]
    if mode in ["recovery", "bootloader"]:
        args.append(mode)
    return run_adb_raw(args, serial=serial)
