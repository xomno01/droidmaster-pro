# -*- coding: utf-8 -*-
"""
DroidMaster Core Engine
Provides high-performance, asynchronous ADB & Scrcpy wrappers for Android device control.
"""

import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
from typing import List, Dict, Optional, Tuple, Any, Union


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
        "cpu": "--%",
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
            "echo ===WIN===; dumpsys window; "
            "echo ===CPU===; dumpsys cpuinfo | grep \"TOTAL:\" | head -n 1"
        )
    elif dynamic_only:
        # Dynamic-only requested without pre-existing cache -> query dynamic parameters only
        batch_script = (
            "echo ===BATTERY===; dumpsys battery; "
            "echo ===IP===; ip route; "
            "echo ===WIN===; dumpsys window; "
            "echo ===CPU===; dumpsys cpuinfo | grep \"TOTAL:\" | head -n 1"
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
            "echo ===SU===; which su; "
            "echo ===CPU===; dumpsys cpuinfo | grep \"TOTAL:\" | head -n 1"
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

    # 6. CPU Usage Telemetry
    cpu_out = sections.get("CPU", "").strip()
    if cpu_out:
        cpu_m = re.search(r"(\d+(?:\.\d+)?%)\s*TOTAL", cpu_out, re.IGNORECASE)
        if not cpu_m:
            cpu_m = re.search(r"TOTAL:\s*(\d+(?:\.\d+)?%)", cpu_out, re.IGNORECASE)
        if not cpu_m:
            cpu_m = re.search(r"(\d+(?:\.\d+)?%)", cpu_out)
        if cpu_m:
            info["cpu"] = cpu_m.group(1).strip()

    return info


# ==============================================================================
# Windows Job Object Process Binding (Prevent Zombie / Orphan Child Processes)
# ==============================================================================

_WINDOWS_JOB_OBJECT = None

def get_windows_job_object():
    """Retrieve or initialize a global Windows Job Object configured with
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE. Guarantees that all child processes
    (such as scrcpy.exe) are automatically killed by Windows kernel if the
    parent application exits for any reason (crash, user exit, kill).
    """
    global _WINDOWS_JOB_OBJECT
    if os.name != 'nt':
        return None
    if _WINDOWS_JOB_OBJECT is not None:
        return _WINDOWS_JOB_OBJECT

    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        JobObjectExtendedLimitInformation = 9

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('PerProcessUserTimeLimit', wintypes.LARGE_INTEGER),
                ('PerJobUserTimeLimit', wintypes.LARGE_INTEGER),
                ('LimitFlags', wintypes.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t),
                ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wintypes.DWORD),
                ('Affinity', ctypes.c_size_t),
                ('PriorityClass', wintypes.DWORD),
                ('SchedulingClass', wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ('ReadOperationCount', ctypes.c_ulonglong),
                ('WriteOperationCount', ctypes.c_ulonglong),
                ('OtherOperationCount', ctypes.c_ulonglong),
                ('ReadTransferCount', ctypes.c_ulonglong),
                ('WriteTransferCount', ctypes.c_ulonglong),
                ('OtherTransferCount', ctypes.c_ulonglong),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ('IoCounters', IO_COUNTERS),
                ('ProcessMemoryLimit', ctypes.c_size_t),
                ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryLimit', ctypes.c_size_t),
                ('PeakJobMemoryLimit', ctypes.c_size_t),
            ]

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        ret = kernel32.SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info)
        )
        if ret:
            _WINDOWS_JOB_OBJECT = job
            return _WINDOWS_JOB_OBJECT
    except Exception:
        pass
    return None


def assign_process_to_job(proc: subprocess.Popen) -> bool:
    """Assign a subprocess.Popen process to the global Windows Job Object."""
    if os.name != 'nt' or proc is None:
        return False
    job = get_windows_job_object()
    if not job:
        return False
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = getattr(proc, "_handle", None)
        if handle:
            return bool(kernel32.AssignProcessToJobObject(job, int(handle)))
    except Exception:
        pass
    return False


# ==============================================================================
# Screen Mirroring (Scrcpy)
# ==============================================================================

def launch_scrcpy(serial: str, options: Dict) -> Optional[subprocess.Popen]:
    """Launch scrcpy with custom user options.
    If the specified serial is disconnected (e.g. user unplugged USB cable after enabling Wi-Fi),
    automatically redirects to the active Wi-Fi or available device.
    Automatically binds the process to the Windows Job Object so it is guaranteed
    to terminate when the parent application closes.
    """
    if not os.path.exists(SCRCPY_PATH):
        return None

    target_serial = serial
    try:
        devs = list_devices()
        active_serials = [d["serial"] for d in devs if d.get("state") == "device"]
        if active_serials and target_serial not in active_serials:
            wifi_serials = [s for s in active_serials if ":" in s]
            target_serial = wifi_serials[0] if wifi_serials else active_serials[0]
    except Exception:
        pass

    cmd = [SCRCPY_PATH, "-s", target_serial]

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

    title = options.get("title", f"DroidMaster // {target_serial}")
    cmd.extend(["--window-title", title])
    cmd.extend(["--window-width", "420"])

    try:
        scrcpy_dir = os.path.dirname(os.path.abspath(SCRCPY_PATH)) if (SCRCPY_PATH and os.path.exists(SCRCPY_PATH)) else (BIN_DIR if BIN_DIR else None)
        proc = subprocess.Popen(
            cmd,
            cwd=scrcpy_dir,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        if proc:
            assign_process_to_job(proc)
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

def take_screenshot_bytes(serial: str, timeout: int = 15) -> Optional[bytes]:
    """Capture screen directly via exec-out screencap -p and return raw PNG bytes in-memory.
    Returns raw bytes starting with b'\x89PNG' if successful, or None on failure.
    Runs purely in RAM without writing temporary files.
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
            timeout=timeout,
            startupinfo=startupinfo
        )

        if proc.returncode == 0 and proc.stdout.startswith(b'\x89PNG'):
            return proc.stdout
        return None
    except Exception:
        return None


def take_screenshot(serial: str, output_path: Optional[str] = None) -> Optional[bytes]:
    """Capture screen and return raw PNG bytes.
    If output_path is provided, also saves the PNG bytes to disk.
    Always returns raw bytes to allow GUI preview (QPixmap) or clipboard copy.
    """
    data = take_screenshot_bytes(serial)
    if data and output_path:
        try:
            parent_dir = os.path.dirname(os.path.abspath(output_path))
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)
        except Exception:
            return None
    return data


# ==============================================================================
# App Management & Networking
# ==============================================================================

def install_apk(serial: str, apk_path: str) -> Tuple[bool, str]:
    """Install an APK file onto the target device."""
    code, stdout, stderr = run_adb_raw(["install", "-r", apk_path], timeout=60, serial=serial)
    if code == 0 and "Success" in stdout:
        return True, "Cài đặt ứng dụng thành công!"
    return False, stdout or stderr or "Lỗi cài đặt APK"


def connect_wifi(
    serial: str,
    ip: Optional[str] = None,
    port: int = 5555,
    check: bool = False
) -> Tuple[bool, str]:
    """Enable TCP/IP wireless debugging and connect over Wi-Fi.
    Checks return code and stdout/stderr of 'adb tcpip <port>' thoroughly before calling 'adb connect'.
    If tcpip fails, returns (False, error_msg) or raises ADBError if check=True.
    Automatically resolves target IP if omitted or passed positionally as port.
    """
    # Handle positional invocation where port is 2nd arg: connect_wifi(serial, 5555)
    if isinstance(ip, int) or (isinstance(ip, str) and ip.isdigit()):
        port = int(ip)
        ip = None

    # Step 1: Execute adb tcpip <port>
    code, out, err = run_adb_raw(["tcpip", str(port)], serial=serial)
    out_lower = (out or "").lower()
    err_lower = (err or "").lower()
    combined_err = (err or out).strip()

    is_tcpip_ok = (
        code == 0
        and not any(term in err_lower for term in ["error", "device offline", "device not found", "cannot", "failed", "closed"])
        and not any(term in out_lower for term in ["error", "device offline", "device not found", "cannot", "failed"])
    )

    if not is_tcpip_ok:
        err_msg = combined_err or f"Lệnh 'adb tcpip {port}' thất bại với mã lỗi {code}"
        if check:
            raise ADBError(err_msg, returncode=code, stdout=out, stderr=err)
        return False, f"Lỗi kích hoạt TCP/IP cổng {port}: {err_msg}"

    # Step 2: Allow ADB daemon on Android device to rebind TCP socket
    import time
    time.sleep(1.0)

    # Step 3: Resolve device IP address if not supplied
    target_ip = ip
    if not target_ip or target_ip == "Unknown":
        try:
            info = get_device_info(serial, dynamic_only=True)
            target_ip = info.get("ip")
        except Exception:
            pass

    if not target_ip or target_ip == "Unknown":
        err_msg = f"Không xác định được địa chỉ IP của thiết bị {serial} để kết nối Wi-Fi."
        if check:
            raise ADBError(err_msg, returncode=-1)
        return False, err_msg

    # Step 4: Perform adb connect <ip>:<port>
    endpoint = f"{target_ip}:{port}"
    c_code, c_out, c_err = run_adb_raw(["connect", endpoint])
    c_combined = (c_out or c_err).strip()

    if "connected to" in c_combined.lower():
        save_config("last_wifi_endpoint", endpoint)
        return True, f"Đã kết nối không dây thành công tới {endpoint}!"

    err_msg = c_combined or f"Không thể kết nối Wi-Fi tới {endpoint}"
    if check:
        raise ADBError(err_msg, returncode=c_code, stdout=c_out, stderr=c_err)
    return False, err_msg


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config() -> Dict[str, Any]:
    """Load persistent configuration dictionary."""
    try:
        if os.path.isfile(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_config(key: str, value: Any) -> None:
    """Save persistent configuration key-value pair."""
    try:
        cfg = load_config()
        cfg[key] = value
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def connect_endpoint(endpoint: str, timeout: int = 5, check: bool = False) -> Tuple[bool, str]:
    """Connect directly to a TCP/IP endpoint without requiring an existing USB serial.
    If port is omitted, defaults to 5555.
    """
    target = endpoint.strip()
    if not target:
        return False, "Địa chỉ IP / endpoint không hợp lệ."
    if ":" not in target:
        target = f"{target}:5555"

    code, out, err = run_adb_raw(["connect", target], timeout=timeout)
    combined = (out or err).strip()
    if "connected to" in combined.lower():
        save_config("last_wifi_endpoint", target)
        return True, f"Đã kết nối không dây thành công tới {target}!"

    err_msg = combined or f"Không thể kết nối Wi-Fi tới {target}"
    if check:
        raise ADBError(err_msg, returncode=code, stdout=out, stderr=err)
    return False, err_msg


def disconnect_endpoint(endpoint: str = None, timeout: int = 5) -> Tuple[bool, str]:
    """Disconnect a TCP/IP endpoint. If endpoint is None, disconnects all."""
    cmd = ["disconnect"]
    if endpoint and endpoint.strip():
        cmd.append(endpoint.strip())
    code, out, err = run_adb_raw(cmd, timeout=timeout)
    combined = (out or err).strip()
    if code == 0 or "disconnected" in combined.lower():
        return True, combined or f"Đã ngắt kết nối {endpoint or 'tất cả'}"
    return False, combined or "Ngắt kết nối thất bại"


def switch_to_wifi(serial: str, ip: str, port: int = 5555, check: bool = False) -> Tuple[bool, str]:
    """Enable TCP/IP wireless debugging and connect over Wi-Fi.
    Maintained for backward compatibility; delegates to connect_wifi.
    """
    return connect_wifi(serial=serial, ip=ip, port=port, check=check)


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


def load_binary_manifest(manifest_path: Optional[str] = None) -> Dict:
    """Load and return the binary integrity manifest from bin/manifest.json or given path."""
    if not manifest_path:
        bin_dir = BIN_DIR or os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
        manifest_path = os.path.join(bin_dir, "manifest.json")
    if not os.path.isfile(manifest_path):
        return {}
    import json
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "files" in data and isinstance(data["files"], dict):
                return data["files"]
            return data
    except Exception:
        return {}


def verify_binary_manifest(manifest_path: Optional[str] = None) -> Dict[str, Any]:
    """Read bin/manifest.json (if present), cross-check the real SHA-256 hashes
    of files in the bin directory, and return a structured dictionary with verification results.
    """
    import hashlib
    import json

    # 1. Locate manifest file
    candidates = []
    if manifest_path:
        candidates.append(manifest_path)
    else:
        if BIN_DIR:
            candidates.append(os.path.join(BIN_DIR, "manifest.json"))
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "manifest.json"))
        candidates.append(os.path.join(os.getcwd(), "bin", "manifest.json"))

    target_manifest = None
    for c in candidates:
        if c and os.path.isfile(c):
            target_manifest = os.path.abspath(c)
            break

    if not target_manifest:
        return {
            "valid": False,
            "manifest_found": False,
            "checked_count": 0,
            "files": {},
            "errors": [f"Không tìm thấy tệp manifest.json tại các đường dẫn: {candidates}"],
            "message": "Không tìm thấy tệp bin/manifest.json."
        }

    # 2. Parse JSON
    try:
        with open(target_manifest, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        return {
            "valid": False,
            "manifest_found": True,
            "checked_count": 0,
            "files": {},
            "errors": [f"Lỗi đọc hoặc phân tích manifest.json: {str(e)}"],
            "message": f"Tệp manifest.json không hợp lệ: {str(e)}"
        }

    # 3. Extract expected files and SHA-256 hashes
    expected_files: Dict[str, str] = {}
    if isinstance(raw_data, dict):
        if "files" in raw_data and isinstance(raw_data["files"], dict):
            for k, v in raw_data["files"].items():
                if isinstance(v, str):
                    expected_files[k] = v.strip().lower()
                elif isinstance(v, dict) and "sha256" in v:
                    expected_files[k] = str(v["sha256"]).strip().lower()
        else:
            for k, v in raw_data.items():
                if isinstance(v, str) and len(v.strip()) == 64:
                    expected_files[k] = v.strip().lower()
                elif isinstance(v, dict) and "sha256" in v:
                    expected_files[k] = str(v["sha256"]).strip().lower()
    elif isinstance(raw_data, list):
        for item in raw_data:
            if isinstance(item, dict) and "file" in item and "sha256" in item:
                expected_files[item["file"]] = str(item["sha256"]).strip().lower()

    if not expected_files:
        return {
            "valid": False,
            "manifest_found": True,
            "checked_count": 0,
            "files": {},
            "errors": ["Tệp manifest.json không chứa danh sách mã băm tệp hợp lệ."],
            "message": "Không có tệp nào được định nghĩa trong manifest.json."
        }

    # 4. Check actual file hashes
    manifest_dir = os.path.dirname(target_manifest)
    file_details: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    all_matched = True

    for filename, exp_hash in expected_files.items():
        file_path = os.path.join(manifest_dir, filename)
        if not os.path.isfile(file_path):
            file_details[filename] = {
                "status": "missing",
                "expected_sha256": exp_hash,
                "actual_sha256": None,
                "path": file_path
            }
            errors.append(f"Tệp không tồn tại: {filename}")
            all_matched = False
            continue

        try:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as bf:
                for chunk in iter(lambda: bf.read(65536), b""):
                    hasher.update(chunk)
            act_hash = hasher.hexdigest().lower()

            if act_hash == exp_hash:
                file_details[filename] = {
                    "status": "ok",
                    "expected_sha256": exp_hash,
                    "actual_sha256": act_hash,
                    "path": file_path
                }
            else:
                file_details[filename] = {
                    "status": "mismatch",
                    "expected_sha256": exp_hash,
                    "actual_sha256": act_hash,
                    "path": file_path
                }
                errors.append(f"Mã băm SHA-256 không khớp cho {filename}: kỳ vọng {exp_hash[:12]}..., thực tế {act_hash[:12]}...")
                all_matched = False
        except Exception as e:
            file_details[filename] = {
                "status": "error",
                "expected_sha256": exp_hash,
                "actual_sha256": None,
                "path": file_path
            }
            errors.append(f"Lỗi khi kiểm tra băm {filename}: {str(e)}")
            all_matched = False

    is_valid = all_matched and len(errors) == 0
    return {
        "valid": is_valid,
        "manifest_found": True,
        "checked_count": len(expected_files),
        "files": file_details,
        "errors": errors,
        "message": f"Đối soát thành công {len(expected_files)}/{len(expected_files)} tệp nhị phân chuẩn 100%!" if is_valid else f"Phát hiện {len(errors)} lỗi trong quá trình đối soát tệp nhị phân."
    }


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
    "take_screenshot_bytes",
    "install_apk",
    "switch_to_wifi",
    "connect_wifi",
    "get_windows_job_object",
    "assign_process_to_job",
    "load_binary_manifest",
    "verify_binary_manifest",
    "reboot",
    "BIN_DIR",
    "ADB_PATH",
    "SCRCPY_PATH",
]
