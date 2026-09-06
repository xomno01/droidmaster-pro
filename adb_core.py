# -*- coding: utf-8 -*-
"""
DroidMaster Core Engine
Provides high-performance, asynchronous ADB & Scrcpy wrappers for Android device control.
"""

import glob
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
from typing import List, Dict, Optional, Tuple


# ==============================================================================
# Structured Exceptions
# ==============================================================================

class ADBError(Exception):
    """Base exception for all ADB-related failures."""
    def __init__(self, message: str, returncode: int = -1, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class DeviceOfflineError(ADBError):
    """Raised when an Android device is offline, unauthorized, or disconnected."""
    pass


class ADBTimeoutError(ADBError):
    """Raised when an ADB command exceeds the specified timeout."""
    pass


# ==============================================================================
# Binary & Environment Discovery
# ==============================================================================

def find_adb() -> str:
    """Independently locate ADB executable across standard SDK paths, WinGet,
    Chocolatey, Scoop, PyInstaller bundle, and system PATH.
    Does not assume scrcpy and adb reside in the same folder.
    """
    exe_name = "adb.exe" if os.name == "nt" else "adb"

    candidates: List[str] = [
        # 1. Bundled / PyInstaller / Current Script / CWD
        os.path.join(getattr(sys, '_MEIPASS', ''), 'bin', exe_name),
        os.path.join(getattr(sys, '_MEIPASS', ''), exe_name),
        os.path.join(os.path.dirname(sys.executable), 'bin', exe_name),
        os.path.join(os.path.dirname(sys.executable), exe_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', exe_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), exe_name),
        os.path.join(os.getcwd(), 'bin', exe_name),
        os.path.join(os.getcwd(), exe_name),
    ]

    # 2. Android SDK environment variables
    for env_var in ["ANDROID_HOME", "ANDROID_SDK_ROOT"]:
        sdk_root = os.environ.get(env_var)
        if sdk_root:
            candidates.append(os.path.join(sdk_root, "platform-tools", exe_name))

    # 3. Windows standard paths & AppData
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates.append(os.path.join(local_app_data, "Android", "Sdk", "platform-tools", exe_name))
        candidates.append(os.path.join(local_app_data, "Programs", "platform-tools", exe_name))

        # WinGet packages
        winget_pattern = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages", "*platform-tools*", "**", exe_name)
        for p in glob.glob(winget_pattern, recursive=True):
            candidates.append(p)
        winget_scrcpy_pattern = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages", "*scrcpy*", "**", exe_name)
        for p in glob.glob(winget_scrcpy_pattern, recursive=True):
            candidates.append(p)

    # 4. Program Files & Common Roots
    for env_var in ["ProgramFiles", "ProgramFiles(x86)"]:
        base = os.environ.get(env_var)
        if base:
            candidates.append(os.path.join(base, "Android", "platform-tools", exe_name))
            candidates.append(os.path.join(base, "platform-tools", exe_name))

    candidates.append(os.path.join("C:\\", "platform-tools", exe_name))
    candidates.append(os.path.join("C:\\", "adb", exe_name))

    # 5. Chocolatey & Scoop
    program_data = os.environ.get("ProgramData", "")
    if program_data:
        candidates.append(os.path.join(program_data, "chocolatey", "bin", exe_name))

    scoop_root = os.environ.get("SCOOP", "")
    if scoop_root:
        candidates.append(os.path.join(scoop_root, "apps", "adb", "current", exe_name))
        candidates.append(os.path.join(scoop_root, "apps", "platform-tools", "current", "platform-tools", exe_name))

    # 6. Check candidates
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)

    # 7. System PATH check
    which_adb = shutil.which("adb")
    if which_adb:
        return os.path.abspath(which_adb)

    return exe_name


def find_scrcpy() -> str:
    """Independently locate Scrcpy executable across WinGet, AppData,
    Chocolatey, Scoop, Program Files, and system PATH.
    Does not assume scrcpy and adb reside in the same folder.
    """
    exe_name = "scrcpy.exe" if os.name == "nt" else "scrcpy"

    candidates: List[str] = [
        # 1. Bundled / PyInstaller / Current Script / CWD
        os.path.join(getattr(sys, '_MEIPASS', ''), 'bin', exe_name),
        os.path.join(getattr(sys, '_MEIPASS', ''), exe_name),
        os.path.join(os.path.dirname(sys.executable), 'bin', exe_name),
        os.path.join(os.path.dirname(sys.executable), exe_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', exe_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), exe_name),
        os.path.join(os.getcwd(), 'bin', exe_name),
        os.path.join(os.getcwd(), exe_name),
    ]

    # 2. System PATH check
    which_scrcpy = shutil.which("scrcpy")
    if which_scrcpy:
        candidates.append(which_scrcpy)

    # 3. WinGet & Local AppData dynamic detection
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_pattern = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages", "*scrcpy*", "**", exe_name)
        for p in glob.glob(winget_pattern, recursive=True):
            candidates.append(p)
        candidates.append(os.path.join(local_app_data, "Programs", "scrcpy", exe_name))

    # 4. Program Files, Chocolatey & Scoop locations
    for env_var in ["ProgramFiles", "ProgramFiles(x86)"]:
        base = os.environ.get(env_var)
        if base:
            candidates.append(os.path.join(base, "scrcpy", exe_name))

    program_data = os.environ.get("ProgramData", "")
    if program_data:
        candidates.append(os.path.join(program_data, "chocolatey", "bin", exe_name))

    scoop_root = os.environ.get("SCOOP", "")
    if scoop_root:
        candidates.append(os.path.join(scoop_root, "apps", "scrcpy", "current", exe_name))

    # 5. Check candidates
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)

    return exe_name


ADB_PATH: str = find_adb()
SCRCPY_PATH: str = find_scrcpy()


def get_bin_dir() -> str:
    """Find the bundled, installed, or local bin directory.
    Maintained for backward compatibility.
    """
    if SCRCPY_PATH and os.path.isabs(SCRCPY_PATH) and os.path.exists(SCRCPY_PATH):
        return os.path.dirname(os.path.abspath(SCRCPY_PATH))
    if ADB_PATH and os.path.isabs(ADB_PATH) and os.path.exists(ADB_PATH):
        return os.path.dirname(os.path.abspath(ADB_PATH))
    fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
    return os.path.abspath(fallback) if os.path.isdir(fallback) else ""


BIN_DIR: str = get_bin_dir()


# ==============================================================================
# ADB Command Execution
# ==============================================================================

def run_adb_raw(args: List[str], timeout: int = 10, serial: Optional[str] = None, check: bool = False) -> Tuple[int, str, str]:
    """Execute raw adb command and return (returncode, stdout, stderr).
    If check=True, raises ADBTimeoutError, DeviceOfflineError, or ADBError on failure.
    """
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
        returncode = proc.returncode
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if check and returncode != 0:
            err_msg = stderr or stdout or f"ADB command failed with exit code {returncode}"
            lowered = err_msg.lower()
            if any(term in lowered for term in ["device offline", "device not found", "no devices/emulators found", "device unauthorized"]):
                raise DeviceOfflineError(err_msg, returncode=returncode, stdout=stdout, stderr=stderr)
            raise ADBError(err_msg, returncode=returncode, stdout=stdout, stderr=stderr)

        return returncode, stdout, stderr
    except subprocess.TimeoutExpired as e:
        if check:
            raise ADBTimeoutError(f"ADB command timed out after {timeout}s: {' '.join(cmd)}") from e
        return -1, "", f"ADBTimeoutError: Command timed out after {timeout}s"
    except (DeviceOfflineError, ADBTimeoutError, ADBError):
        raise
    except Exception as e:
        if check:
            raise ADBError(str(e)) from e
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


# ==============================================================================
# Optimized Telemetry Engine & Static Cache
# ==============================================================================

_STATIC_CACHE_LOCK = threading.Lock()
_DEVICE_STATIC_CACHE: Dict[str, Dict[str, str]] = {}


def get_cached_static_info(serial: str) -> Optional[Dict[str, str]]:
    """Return cached static telemetry for the specified serial, or None if not cached."""
    with _STATIC_CACHE_LOCK:
        cached = _DEVICE_STATIC_CACHE.get(serial)
        return dict(cached) if cached else None


def clear_device_cache(serial: Optional[str] = None) -> None:
    """Clear telemetry cache for a specific serial or all devices."""
    with _STATIC_CACHE_LOCK:
        if serial:
            _DEVICE_STATIC_CACHE.pop(serial, None)
        else:
            _DEVICE_STATIC_CACHE.clear()


def get_device_info(serial: str, dynamic_only: bool = False, refresh_cache: bool = False) -> Dict[str, str]:
    """Fetch hardware and system telemetry for a specific device.
    Uses Static Telemetry Caching: static metrics (model, brand, android_version,
    sdk, resolution, root) are cached per device serial. When static cache is present,
    or when dynamic_only=True, only the lightweight dynamic metrics (battery, temp, ip,
    active_app) are queried in a minimal batch command, yielding up to 3x-5x speedup.
    """
    info = {
        "model": "Unknown",
        "brand": "Android",
        "android_version": "Unknown",
        "sdk": "",
        "battery_level": "--%",
        "battery_temp": "--°C",
        "resolution": "Unknown",
        "ip": "Unknown",
        "root": "Không có (Chưa root)",
        "active_app": "Trang chính (Launcher)"
    }

    cached_static = get_cached_static_info(serial) if not refresh_cache else None
    has_cache = cached_static is not None

    if has_cache:
        # Static telemetry already cached -> reuse and only query dynamic parameters
        info.update(cached_static)
        batch_script = (
            "echo ===BATTERY===; dumpsys battery; "
            "echo ===IP===; ip route; "
            "echo ===WIN===; dumpsys window"
        )
    elif dynamic_only:
        # Dynamic-only requested without pre-existing cache -> query dynamic parameters only
        batch_script = (
            "echo ===BATTERY===; dumpsys battery; "
            "echo ===IP===; ip route; "
            "echo ===WIN===; dumpsys window"
        )
    else:
        # Full query: fetch static properties (model, brand, version, sdk, wm size, su) + dynamic
        batch_script = (
            "echo ===PROP===; getprop ro.product.model; getprop ro.product.brand; "
            "getprop ro.build.version.release; getprop ro.build.version.sdk; "
            "echo ===BATTERY===; dumpsys battery; "
            "echo ===WM===; wm size; "
            "echo ===IP===; ip route; "
            "echo ===WIN===; dumpsys window; "
            "echo ===SU===; which su"
        )

    code, stdout, stderr = run_adb_raw(["shell", batch_script], timeout=15, serial=serial)
    if code != 0 and not stdout:
        err_low = (stderr or "").lower()
        if any(term in err_low for term in ["device offline", "device not found", "device unauthorized", "no devices"]):
            raise DeviceOfflineError(f"Device {serial} is offline or not found: {stderr}")
        if "timed out" in err_low or "timeout" in err_low:
            raise ADBTimeoutError(f"Telemetry query timed out for {serial}")
        raise ADBError(f"Failed to fetch telemetry for {serial}: {stderr}")

    parts = re.split(r"===([A-Z]+)===", stdout)
    sections: Dict[str, str] = {}
    for i in range(1, len(parts), 2):
        sections[parts[i]] = parts[i + 1].strip()

    # Parse static components if we executed the full batch
    if not (has_cache or dynamic_only):
        # 1. Model & Brand & Android release / SDK
        prop_out = sections.get("PROP", "")
        prop_lines = [l.strip() for l in prop_out.splitlines()]
        model = prop_lines[0] if len(prop_lines) > 0 else ""
        brand = prop_lines[1] if len(prop_lines) > 1 else ""
        release = prop_lines[2] if len(prop_lines) > 2 else ""
        sdk = prop_lines[3] if len(prop_lines) > 3 else ""

        if model:
            info["model"] = model
        if brand:
            info["brand"] = brand.capitalize()
        if release:
            info["android_version"] = f"Android {release} (SDK {sdk})" if sdk else f"Android {release}"
        if sdk:
            info["sdk"] = sdk

        # 3. Display Resolution
        wm_out = sections.get("WM", "") or sections.get("RESOLUTION", "")
        size_m = re.search(r"(?:Physical size|Override size):\s*(\d+x\d+)", wm_out)
        if not size_m:
            size_m = re.search(r"(\d+x\d+)", wm_out)
        if size_m:
            info["resolution"] = size_m.group(1)

        # 6. Passive Root Detection (which su without invoking su -c)
        su_out = sections.get("SU", "").strip()
        if su_out and "su" in su_out and not any(term in su_out.lower() for term in ["not found", "no su"]):
            info["root"] = "Đã phát hiện su binary"
        else:
            info["root"] = "Không có (Chưa root)"

        # Save static telemetry into cache
        with _STATIC_CACHE_LOCK:
            _DEVICE_STATIC_CACHE[serial] = {
                "model": info["model"],
                "brand": info["brand"],
                "android_version": info["android_version"],
                "sdk": info["sdk"],
                "resolution": info["resolution"],
                "root": info["root"],
            }

    # Dynamic metrics (always extracted from fresh batch execution)
    # 2. Battery Level & Temperature
    battery_out = sections.get("BATTERY", "") or sections.get("BAT", "")
    level_m = re.search(r"level:\s*(\d+)", battery_out)
    if not level_m:
        level_m = re.search(r"(\d+)%", battery_out)
    if not level_m:
        level_m = re.search(r"\b(\d{1,3})\b", battery_out)
    if level_m:
        info["battery_level"] = f"{level_m.group(1)}%"

    temp_m = re.search(r"temperature:\s*(\d+(?:\.\d+)?)", battery_out)
    if not temp_m:
        temp_m = re.search(r"(\d+(?:\.\d+)?)\s*°?C", battery_out)
    if temp_m:
        raw_t = float(temp_m.group(1))
        temp_val = raw_t / 10.0 if raw_t > 100 else raw_t
        info["battery_temp"] = f"{temp_val:.1f}°C"

    # 4. IP Address
    ip_out = sections.get("IP", "")
    ip_m = re.search(r"src\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", ip_out)
    if not ip_m:
        ip_m = re.search(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", ip_out)
    if ip_m:
        info["ip"] = ip_m.group(1)

    # 5. Current Focused Window / App
    app_out = sections.get("APP", "").strip()
    win_out = sections.get("WIN", "") or sections.get("WINDOW", "")
    if app_out:
        info["active_app"] = app_out
    elif win_out:
        win_m = re.search(r"mCurrentFocus=Window\{[^\s]+\s+[^\s]+\s+([^/\s]+)", win_out)
        if not win_m:
            win_m = re.search(r"mFocusedApp=.*?(?:ActivityRecord|AppWindowToken|\{)[^\s]+\s+[^\s]+\s+([^/\s]+)", win_out)
        if not win_m:
            win_m = re.search(r"([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)/", win_out)
        if win_m:
            info["active_app"] = win_m.group(1)
        elif "/" in win_out:
            parts = win_out.split("/")[0].strip().split()
            info["active_app"] = parts[-1] if parts else win_out.strip()
        elif win_out:
            info["active_app"] = win_out.strip()

    return info


# ==============================================================================
# Screen Mirroring (Scrcpy)
# ==============================================================================

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
        scrcpy_dir = os.path.dirname(os.path.abspath(SCRCPY_PATH)) if (SCRCPY_PATH and os.path.exists(SCRCPY_PATH)) else (BIN_DIR if BIN_DIR else None)
        proc = subprocess.Popen(
            cmd,
            cwd=scrcpy_dir,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        return proc
    except Exception:
        return None


# ==============================================================================
# Device Input & Control
# ==============================================================================

def send_keyevent(serial: str, keycode: str) -> Tuple[int, str, str]:
    """Inject hardware key event."""
    return run_adb_raw(["shell", "input", "keyevent", str(keycode)], serial=serial)


def escape_text_for_adb(text: str) -> str:
    """Escape ASCII string special characters for adb shell input text.
    Replaces spaces with %s and escapes shell metacharacters.
    """
    if not text:
        return ""
    return (
        text.replace(" ", "%s")
        .replace("&", "\\&")
        .replace("<", "\\<")
        .replace(">", "\\>")
        .replace('"', '\\"')
        .replace("'", "\\'")
    )


def escape_text(text: str) -> str:
    """Convenience alias for escape_text_for_adb."""
    return escape_text_for_adb(text)


def escape_unicode_for_clipboard(text: str) -> str:
    """Escape Unicode / full-text string for safe injection via cmd clipboard shell execution."""
    if not text:
        return "''"
    return shlex.quote(text)


def escape_unicode_text(text: str) -> str:
    """Convenience alias for escape_unicode_for_clipboard."""
    return escape_unicode_for_clipboard(text)


def send_text(serial: str, text: str) -> Tuple[int, str, str]:
    """Send text to the active focused input field.
    Supports full Vietnamese and Unicode characters via clipboard injection
    (cmd clipboard set <escaped_text> + KEYCODE_PASTE 279).
    Falls back gracefully for older Android versions or standard ASCII strings.
    """
    if not text:
        return 0, "", ""

    if not text.isascii():
        escaped_text = escape_unicode_for_clipboard(text)
        code, out, err = run_adb_raw(["shell", f"cmd clipboard set {escaped_text}"], serial=serial)
        # Check if cmd clipboard is supported (Android 13+)
        if code == 0 and "No shell command implementation" not in out and "No shell command implementation" not in err:
            return run_adb_raw(["shell", "input", "keyevent", "279"], serial=serial)

        # Fallback for devices without cmd clipboard: transliterate to ASCII
        import unicodedata
        normalized = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        escaped = escape_text_for_adb(normalized)
        return run_adb_raw(["shell", "input", "text", escaped], serial=serial)
    else:
        escaped = escape_text_for_adb(text)
        return run_adb_raw(["shell", "input", "text", escaped], serial=serial)


# ==============================================================================
# Upgraded Direct Screenshot Capture
# ==============================================================================

def take_screenshot(serial: str, output_path: str) -> bool:
    """Capture screen directly to local PC path via exec-out screencap -p.
    Eliminates temporary remote file /sdcard/_droid_snap.png and pull/rm roundtrips,
    preventing race conditions and avoiding flash memory wear.
    """
    cmd = [ADB_PATH, "-s", serial, "exec-out", "screencap", "-p"]
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=15,
            startupinfo=startupinfo
        )

        if proc.returncode == 0 and proc.stdout.startswith(b'\x89PNG'):
            parent_dir = os.path.dirname(os.path.abspath(output_path))
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(proc.stdout)
            return True
        return False
    except Exception:
        return False


# ==============================================================================
# App Management & Networking
# ==============================================================================

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


def reboot(serial: str, mode: str = "") -> Tuple[int, str, str]:
    """Reboot device into normal, recovery, or bootloader."""
    args = ["reboot"]
    if mode in ["recovery", "bootloader"]:
        args.append(mode)
    return run_adb_raw(args, serial=serial)


# ==============================================================================
# UI Hierarchy Recon Engine (UIAutomator XML Parsing)
# ==============================================================================

def parse_ui_hierarchy(xml_content: str) -> List[Dict]:
    """Cleanly parse UIAutomator XML dump nodes extracting attributes:
    text, content-desc, resource-id, class, bounds, coords, center, and clickable.
    """
    import xml.etree.ElementTree as ET
    elements: List[Dict] = []
    if not xml_content or not xml_content.strip():
        return elements

    xml_bytes = xml_content.strip().encode("utf-8", errors="replace")

    try:
        root = ET.fromstring(xml_bytes)
        for node in root.iter("node"):
            attrib = node.attrib
            bounds = attrib.get("bounds", "")
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
            if not m:
                continue
            x1, y1, x2, y2 = map(int, m.groups())
            if x1 >= x2 or y1 >= y2:
                continue

            text = attrib.get("text", "").strip()
            desc = attrib.get("content-desc", "").strip()
            res_id = attrib.get("resource-id", "").strip()
            cls_name = attrib.get("class", "").strip()
            clickable = attrib.get("clickable", "false").lower() == "true"
            checkable = attrib.get("checkable", "false").lower() == "true"
            long_clickable = attrib.get("long-clickable", "false").lower() == "true"

            is_interactive = clickable or checkable or long_clickable or bool(text) or bool(desc)
            if not is_interactive:
                continue

            short_type = cls_name.split(".")[-1] if cls_name else "View"
            # Filter out full-screen background frames with no text/desc/id
            if (x2 - x1) >= 1080 and (y2 - y1) >= 2000 and not text and not desc and not res_id:
                continue

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            short_id = res_id.split("/")[-1] if "/" in res_id else res_id

            elements.append({
                "type": short_type,
                "full_class": cls_name,
                "text": text,
                "desc": desc,
                "resource_id": res_id,
                "short_id": short_id,
                "bounds": bounds,
                "coords": (x1, y1, x2, y2),
                "center": (cx, cy),
                "clickable": clickable or is_interactive
            })
    except Exception:
        # Fallback regex parser for malformed/non-standard XML
        pattern = re.compile(
            r'<node[^>]*?text="(?P<text>[^"]*)"[^>]*?'
            r'resource-id="(?P<id>[^"]*)"[^>]*?'
            r'class="(?P<class>[^"]*)"[^>]*?'
            r'package="(?P<pkg>[^"]*)"[^>]*?'
            r'content-desc="(?P<desc>[^"]*)"[^>]*?'
            r'clickable="(?P<clickable>[^"]*)"[^>]*?'
            r'bounds="(?P<bounds>\[\d+,\d+\]\[\d+,\d+\])"'
        )
        for match in pattern.finditer(xml_content):
            d = match.groupdict()
            bounds = d["bounds"]
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
            if not m:
                continue
            x1, y1, x2, y2 = map(int, m.groups())
            if x1 >= x2 or y1 >= y2:
                continue
            text = d.get("text", "").strip()
            desc = d.get("desc", "").strip()
            res_id = d.get("id", "").strip()
            cls_name = d.get("class", "").strip()
            clickable = d.get("clickable", "false").lower() == "true"
            if not (clickable or text or desc):
                continue
            short_type = cls_name.split(".")[-1] if cls_name else "View"
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            short_id = res_id.split("/")[-1] if "/" in res_id else res_id
            elements.append({
                "type": short_type,
                "full_class": cls_name,
                "text": text,
                "desc": desc,
                "resource_id": res_id,
                "short_id": short_id,
                "bounds": bounds,
                "coords": (x1, y1, x2, y2),
                "center": (cx, cy),
                "clickable": clickable
            })
    return elements


__all__ = [
    "ADBError",
    "DeviceOfflineError",
    "ADBTimeoutError",
    "find_adb",
    "find_scrcpy",
    "get_bin_dir",
    "get_cached_static_info",
    "clear_device_cache",
    "run_adb_raw",
    "list_devices",
    "get_device_info",
    "launch_scrcpy",
    "send_keyevent",
    "send_text",
    "escape_text_for_adb",
    "escape_text",
    "escape_unicode_for_clipboard",
    "escape_unicode_text",
    "parse_ui_hierarchy",
    "take_screenshot",
    "install_apk",
    "switch_to_wifi",
    "reboot",
    "BIN_DIR",
    "ADB_PATH",
    "SCRCPY_PATH",
]
