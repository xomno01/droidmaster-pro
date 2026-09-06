# -*- coding: utf-8 -*-
"""
CYBER_DROID // ADVANCED TACTICAL ANDROID TERMINAL & PROTOCOL BRIDGE
Author: Antigravity Cyber Division / DroidMaster Engineering
Target: Connected Android Subsystem // ADB Protocol Bridge
"""

import os
import sys
import time
import subprocess
import re
import random
import threading
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple

# Ensure current module directory is on sys.path for direct execution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.text import Text

# Import unified engine from adb_core
from adb_core import (
    run_adb_raw,
    list_devices,
    get_device_info,
    send_keyevent,
    send_text,
    take_screenshot,
    reboot,
    switch_to_wifi,
    launch_scrcpy,
)

console = Console()

# Active device context & recon element cache
CURRENT_SERIAL: Optional[str] = None
RECON_ELEMENTS: List[Dict] = []


def get_active_serial() -> Optional[str]:
    """Resolve the active device serial, or select the first connected device."""
    global CURRENT_SERIAL
    if CURRENT_SERIAL:
        return CURRENT_SERIAL
    devs = list_devices()
    if devs:
        CURRENT_SERIAL = devs[0]["serial"]
        return CURRENT_SERIAL
    return None


def run_adb(args: List[str], timeout: int = 10, capture: bool = True, serial: Optional[str] = None) -> str:
    """Convenience wrapper delegating directly to adb_core.run_adb_raw."""
    active = serial or get_active_serial()
    code, stdout, stderr = run_adb_raw(args, timeout=timeout, serial=active)
    if not capture:
        return ""
    return stdout if code == 0 else (stdout or stderr)

def terminal_init_sequence():
    """Authentic terminal subsystem bootstrap sequence."""
    console.clear()
    with Progress(
        SpinnerColumn(spinner_name="dots12", style="bold green"),
        TextColumn("[bold green]{task.description}"),
        BarColumn(bar_width=40, style="green", complete_style="bold bright_green"),
        TextColumn("[bold bright_cyan]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        t1 = progress.add_task("[bold cyan]INITIALIZING PRIVILEGED ADB BRIDGE...", total=100)
        t2 = progress.add_task("[bold green]ESTABLISHING SECURE PROTOCOL CHANNEL...", total=100)
        t3 = progress.add_task("[bold magenta]SYNCHRONIZING SUBSYSTEM TELEMETRY...", total=100)

        while not progress.finished:
            time.sleep(0.015)
            progress.update(t1, advance=random.randint(4, 8))
            if progress.tasks[0].completed > 40:
                progress.update(t2, advance=random.randint(5, 10))
            if progress.tasks[1].completed > 50:
                progress.update(t3, advance=random.randint(4, 9))

    time.sleep(0.2)
    console.clear()

def print_banner():
    banner_text = """
 [bold bright_green]██████╗██╗   ██╗██████╗ ███████╗██████╗       ██████╗ ██████╗  ██████╗ ██╗██████╗ [/]
 [bold bright_green]██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗      ██╔══██╗██╔══██╗██╔═══██╗██║██╔══██╗[/]
 [bold bright_cyan]██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝█████╗██║  ██║██████╔╝██║   ██║██║██║  ██║[/]
 [bold bright_cyan]██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗╚════╝██║  ██║██╔══██╗██║   ██║██║██║  ██║[/]
 [bold bright_magenta]╚██████╗   ██║   ██████╔╝███████╗██║  ██║      ██████╔╝██║  ██║╚██████╔╝██║██████╔╝[/]
 [bold bright_magenta] ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═════╝ [/]
               [bold yellow]───[ TACTICAL ADB INTERFACE // PROTOCOL BRIDGE // DROIDMASTER ]───[/]
    """
    console.print(banner_text)

def get_device_telemetry(serial: Optional[str] = None) -> Dict[str, str]:
    """Fetch hardware and system telemetry via adb_core."""
    active = serial or get_active_serial() or ""
    info = get_device_info(active)

    model = info.get("model", "Android Device")
    battery = info.get("battery_level", "Unknown")
    temp = info.get("battery_temp", "Unknown")
    ip = info.get("ip", "127.0.0.1")
    active_app = info.get("active_app", "Launcher")
    resolution = info.get("resolution", "Unknown")
    version = info.get("android_version", "Unknown")

    return {
        "model": model,
        "battery": battery,
        "temp": temp,
        "ip": ip,
        "active": active_app,
        "security": "INITIALIZED / PRIVILEGED_ADB",
        "resolution": resolution,
        "version": version,
        "serial": active or "DISCONNECTED"
    }

def print_hud(serial: Optional[str] = None):
    tele = get_device_telemetry(serial)
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row(
        f"[bold bright_green]TARGET:[/] [white]{tele['model']} ({tele['serial']})[/]",
        f"[bold bright_cyan]NET IP:[/] [white]{tele['ip']}:5555[/]",
        f"[bold bright_yellow]POWER:[/] [white]{tele['battery']} ({tele['temp']})[/]"
    )
    table.add_row(
        f"[bold bright_magenta]SUBSYSTEM TELEMETRY:[/] [green]{tele['security']}[/]",
        f"[bold bright_cyan]FOCUS APPS:[/] [white]{tele['active']}[/]",
        f"[bold bright_green]STATUS:[/] [bold blink bright_green]● CONNECTED & SYNCHRONIZED[/]"
    )
    console.print(Panel(table, title="[bold bright_green]◈ TACTICAL TELEMETRY HUD ◈[/]", border_style="bright_green"))

def matrix_rain(duration: int = 3):
    """Visual telemetry data stream effect."""
    console.print("[bold green]RENDERING TELEMETRY STREAM MATRIX...[/]")
    katakana = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ0123456789ABCDEF!@#$%^&*"
    width = console.width or 80
    end_time = time.time() + duration
    while time.time() < end_time:
        line = "".join(random.choice(katakana) if random.random() > 0.4 else " " for _ in range(width))
        style = random.choice(["bold green", "bright_green", "green", "white"])
        console.print(f"[{style}]{line}[/]")
        time.sleep(0.04)

def parse_ui_hierarchy(xml_content: str) -> List[Dict]:
    """Cleanly parse UIAutomator XML dump nodes extracting attributes:
    text, content-desc, resource-id, class, bounds, and clickable."""
    elements = []
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
        # Fallback regex parser for non-standard XML
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

def cmd_recon(serial: Optional[str] = None):
    """Dump UIAutomator XML, parse node attributes, and display clickable elements in a clean Rich table."""
    global RECON_ELEMENTS
    active = serial or get_active_serial()

    with console.status("[bold cyan]EXTRACTING ACTIVE UI HIERARCHY TELEMETRY...", spinner="bouncingBar"):
        run_adb_raw(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], serial=active)
        _, xml_content, _ = run_adb_raw(["shell", "cat", "/sdcard/window_dump.xml"], serial=active)
        run_adb_raw(["shell", "rm", "-f", "/sdcard/window_dump.xml"], serial=active)

    if not xml_content or "<hierarchy" not in xml_content:
        console.print("[yellow][!] UI hierarchy dump returned empty content or screen was transitioning. Retrying with compression...[/]")
        run_adb_raw(["shell", "uiautomator", "dump", "--compressed", "/sdcard/window_dump.xml"], serial=active)
        _, xml_content, _ = run_adb_raw(["shell", "cat", "/sdcard/window_dump.xml"], serial=active)
        run_adb_raw(["shell", "rm", "-f", "/sdcard/window_dump.xml"], serial=active)

    if not xml_content or "<hierarchy" not in xml_content:
        console.print("[red][!] Could not retrieve UI hierarchy. Ensure device screen is on and unlocked.[/]")
        return

    elements = parse_ui_hierarchy(xml_content)
    RECON_ELEMENTS = elements

    if not elements:
        console.print("[yellow][!] No interactive elements detected in current window hierarchy.[/]")
        return

    table = Table(
        title="[bold bright_green]◈ RECON TELEMETRY: DISCOVERED UI TARGETS & COORDINATES ◈[/]",
        border_style="cyan",
        header_style="bold cyan"
    )
    table.add_column("Index", style="dim cyan", justify="right", width=6)
    table.add_column("Type", style="bold green", width=14)
    table.add_column("ID / Text", style="bold white")
    table.add_column("Bounds", style="dim white", width=19)
    table.add_column("Center (cx, cy)", style="bold bright_yellow", justify="center", width=16)
    table.add_column("Quick Command", style="bold bright_cyan", width=14)

    max_display = 25
    for idx, elem in enumerate(elements[:max_display], 1):
        elem["index"] = idx
        text = elem["text"]
        desc = elem["desc"]
        short_id = elem["short_id"]

        label_parts = []
        if text:
            label_parts.append(f'"{text}"')
        if desc and desc != text:
            label_parts.append(f'[desc: "{desc}"]')
        if short_id:
            label_parts.append(f'[dim cyan]id/{short_id}[/]')

        label = " ".join(label_parts) if label_parts else "[dim italic]unnamed element[/]"
        cx, cy = elem["center"]
        quick_cmd = f"tap_id {idx}"

        table.add_row(
            str(idx),
            elem["type"],
            label,
            elem["bounds"],
            f"({cx}, {cy})",
            quick_cmd
        )

    console.print(table)
    if len(elements) > max_display:
        console.print(f"[dim]Showing first {max_display} of {len(elements)} elements. Use [bold white]tap_id <idx>[/] or [bold white]tap_text <query>[/] to interact.[/]")
    else:
        console.print(f"[dim]Total {len(elements)} interactive elements indexed. Tap via [bold white]tap_id <idx>[/] or [bold white]tap_text <query>[/].[/]")

def cmd_tap_id(target_arg: str, serial: Optional[str] = None):
    """Click an element discovered by recon using its index or resource ID."""
    global RECON_ELEMENTS
    active = serial or get_active_serial()

    if not RECON_ELEMENTS:
        console.print("[yellow][*] No cached UI elements. Running recon scan first...[/]")
        cmd_recon(active)
        if not RECON_ELEMENTS:
            return

    target_elem = None
    if target_arg.isdigit():
        idx = int(target_arg)
        if 1 <= idx <= len(RECON_ELEMENTS):
            target_elem = RECON_ELEMENTS[idx - 1]
        else:
            console.print(f"[red][!] Index {idx} out of range (1 - {len(RECON_ELEMENTS)}).[/]")
            return
    else:
        # Match by ID or short ID
        for elem in RECON_ELEMENTS:
            if target_arg.lower() in elem["short_id"].lower() or target_arg.lower() in elem["resource_id"].lower():
                target_elem = elem
                break
        if not target_elem:
            console.print(f"[red][!] Element identifier '{target_arg}' not found in cached recon elements.[/]")
            return

    cx, cy = target_elem["center"]
    with console.status(f"[bold green]DISPATCHING INPUT TAP AT ({cx}, {cy})...[/]"):
        run_adb_raw(["shell", "input", "tap", str(cx), str(cy)], serial=active)

    desc_str = target_elem["text"] or target_elem["desc"] or target_elem["short_id"] or target_elem["type"]
    console.print(f"[bold bright_green][✓] Tapped Element #{target_elem.get('index', '?')} [{target_elem['type']}: {desc_str}] at ({cx}, {cy})[/]")

def cmd_tap_text(query: str, serial: Optional[str] = None):
    """Click an element discovered by recon using its text or content description."""
    global RECON_ELEMENTS
    active = serial or get_active_serial()

    if not RECON_ELEMENTS:
        console.print("[yellow][*] No cached UI elements. Running recon scan first...[/]")
        cmd_recon(active)
        if not RECON_ELEMENTS:
            return

    q = query.strip().lower()
    matches = []

    # 1. Exact match in text or desc
    for elem in RECON_ELEMENTS:
        if elem["text"].lower() == q or elem["desc"].lower() == q:
            matches.append(elem)

    # 2. Substring match in text or desc
    if not matches:
        for elem in RECON_ELEMENTS:
            if q in elem["text"].lower() or q in elem["desc"].lower():
                matches.append(elem)

    # 3. Substring match in resource ID
    if not matches:
        for elem in RECON_ELEMENTS:
            if q in elem["short_id"].lower():
                matches.append(elem)

    if not matches:
        console.print(f"[red][!] No element found matching text query '{query}'. Run 'recon' to inspect available UI elements.[/]")
        return

    target = matches[0]
    cx, cy = target["center"]
    with console.status(f"[bold green]DISPATCHING INPUT TAP AT ({cx}, {cy})...[/]"):
        run_adb_raw(["shell", "input", "tap", str(cx), str(cy)], serial=active)

    desc_str = target["text"] or target["desc"] or target["short_id"] or target["type"]
    console.print(f"[bold bright_green][✓] Matched element #{target.get('index', '?')} ('{desc_str}') -> Tapped at ({cx}, {cy})[/]")

def cmd_scrcpy(serial: Optional[str] = None):
    """Deploy hardware-accelerated screen mirror via adb_core.launch_scrcpy."""
    active = serial or get_active_serial() or ""
    console.print("[bold bright_green][+] DEPLOYING HARDWARE ACCELERATED SCREEN MIRROR (ALWAYS ON TOP)...[/]")
    proc = launch_scrcpy(active, {
        "always_on_top": True,
        "title": f"DROIDMASTER // {active or 'DEVICE'}",
        "stay_awake": True
    })
    if proc:
        console.print("[bold cyan][*] Screen Mirror active! Mouse click and keyboard input are synced to device.[/]")
    else:
        console.print("[bold red][!] Could not launch scrcpy. Verify scrcpy installation in bin directory.[/]")

def cmd_apps(serial: Optional[str] = None):
    """Query and display 3rd-party applications installed on the target device."""
    active = serial or get_active_serial()
    with console.status("[bold cyan]QUERYING 3RD-PARTY PACKAGE REGISTRY...", spinner="dots"):
        _, raw, _ = run_adb_raw(["shell", "pm", "list", "packages", "-3"], serial=active)
    packages = [line.replace("package:", "").strip() for line in raw.splitlines() if line.strip()]

    table = Table(title="[bold bright_cyan]◈ TARGET APPLICATION REGISTRY (3RD-PARTY) ◈[/]", border_style="cyan")
    table.add_column("#", style="dim cyan", justify="right")
    table.add_column("Package Identifier", style="bold white")
    table.add_column("Execution Command", style="bold bright_green")

    for idx, pkg in enumerate(packages[:25], 1):
        table.add_row(str(idx), pkg, f"open {pkg}")

    console.print(table)

def main_loop():
    global CURRENT_SERIAL
    terminal_init_sequence()
    print_banner()
    print_hud()

    console.print("""
 [bold bright_cyan]AVAILABLE OPERATIONS:[/]
   [bold bright_green]recon[/]             : Quét phân tích cấu trúc UI & toạ độ các phần tử trên màn hình
   [bold bright_green]tap_id <idx>[/]     : Nhấp vào phần tử UI theo chỉ số Index hoặc ID sau khi recon
   [bold bright_green]tap_text <text>[/]   : Nhấp vào phần tử UI theo nhãn chữ / nội dung văn bản
   [bold bright_green]tap <x> <y>[/]      : Gửi sự kiện chạm vào toạ độ (VD: tap 540 1000)
   [bold bright_green]swipe <dir>[/]      : Vuốt màn hình (up, down, left, right)
   [bold bright_green]type <text>[/]      : Gửi chuỗi ký tự vào trường nhập liệu
   [bold bright_green]key <btn>[/]        : Bấm phím phần cứng (home, back, recents, power, volup, voldown)
   [bold bright_green]snap [file][/]      : Chụp ảnh màn hình thiết bị lưu về máy tính
   [bold bright_green]hud[/] / [bold bright_green]scrcpy[/]       : Bật màn hình gương thời gian thực cạnh IDE (chuột + phím)
   [bold bright_green]apps[/]              : Liệt kê các ứng dụng đã cài đặt trên máy
   [bold bright_green]open <pkg>[/]        : Mở app (VD: open youtube, open camera, open settings)
   [bold bright_green]kill <pkg>[/]        : Buộc dừng tiến trình ứng dụng
   [bold bright_green]devices[/]           : Liệt kê danh sách các thiết bị Android đang kết nối
   [bold bright_green]device <serial>[/]   : Chọn thiết bị mục tiêu làm việc
   [bold bright_green]untether[/]          : Chuyển sang điều khiển không dây Wi-Fi (TCP/IP)
   [bold bright_green]reboot [mode][/]     : Khởi động lại thiết bị (normal, recovery, bootloader)
   [bold bright_green]matrix[/]            : Hiệu ứng luồng dữ liệu Matrix Telemetry
   [bold bright_green]shell <cmd>[/]       : Thực thi lệnh Linux Shell trực tiếp trên Android
   [bold bright_green]cls[/] / [bold bright_green]clear[/]       : Xoá màn hình & nạp lại HUD
   [bold bright_green]exit[/]              : Đóng phiên làm việc Terminal
    """)

    while True:
        try:
            active = get_active_serial() or "droidmaster"
            prompt_label = active.split(":")[0] if ":" in active else active
            cmd_line = console.input(f"[bold bright_green]adb@{prompt_label}[/][white]:[/][bold bright_cyan]~[/][bold yellow]#[/] ").strip()
            if not cmd_line:
                continue

            parts = cmd_line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ["exit", "quit", "q"]:
                console.print("[bold red][!] TERMINATING ADB BRIDGE SESSION... CHANNELS CLOSED.[/]")
                break

            elif cmd in ["cls", "clear"]:
                console.clear()
                print_banner()
                print_hud()

            elif cmd == "matrix":
                matrix_rain(duration=4)

            elif cmd in ["hud", "scrcpy"]:
                cmd_scrcpy()

            elif cmd == "recon":
                cmd_recon()

            elif cmd == "tap_id":
                if not args:
                    console.print("[red][!] Cú pháp: tap_id <index|id>[/]")
                else:
                    cmd_tap_id(args[0])

            elif cmd == "tap_text":
                if not args:
                    console.print("[red][!] Cú pháp: tap_text <nội dung văn bản>[/]")
                else:
                    cmd_tap_text(" ".join(args))

            elif cmd == "apps":
                cmd_apps()

            elif cmd == "devices":
                devs = list_devices()
                if not devs:
                    console.print("[yellow][!] Không tìm thấy thiết bị Android nào đang kết nối.[/]")
                else:
                    table = Table(title="[bold bright_green]◈ CONNECTED ANDROID DEVICES ◈[/]", border_style="cyan")
                    table.add_column("#", style="dim cyan", justify="right")
                    table.add_column("Serial / IP", style="bold white")
                    table.add_column("Model", style="bold cyan")
                    table.add_column("State", style="bold green")
                    table.add_column("Type", style="yellow")
                    for i, d in enumerate(devs, 1):
                        is_cur = " [bold bright_green](active)[/]" if d["serial"] == CURRENT_SERIAL else ""
                        table.add_row(str(i), d["serial"] + is_cur, d["model"], d["state"], d["type"])
                    console.print(table)

            elif cmd == "device":
                if not args:
                    console.print("[red][!] Cú pháp: device <serial|index>[/]")
                else:
                    devs = list_devices()
                    target = args[0]
                    if target.isdigit() and 1 <= int(target) <= len(devs):
                        CURRENT_SERIAL = devs[int(target) - 1]["serial"]
                        console.print(f"[bold bright_green][✓] Target switched to: {CURRENT_SERIAL}[/]")
                    else:
                        CURRENT_SERIAL = target
                        console.print(f"[bold bright_green][✓] Target serial configured: {CURRENT_SERIAL}[/]")

            elif cmd == "tap":
                if len(args) < 2:
                    console.print("[red][!] Cú pháp: tap <x> <y>[/]")
                else:
                    x, y = args[0], args[1]
                    with console.status(f"[bold green]DISPATCHING INPUT TAP AT ({x}, {y})...[/]"):
                        run_adb_raw(["shell", "input", "tap", x, y], serial=get_active_serial())
                    console.print(f"[bold bright_green][✓] Input tap event dispatched at ({x}, {y}).[/]")

            elif cmd == "swipe":
                if not args:
                    console.print("[red][!] Cú pháp: swipe <up|down|left|right>[/]")
                else:
                    direction = args[0].lower()
                    dirs = {
                        "up": ("540", "1600", "540", "600"),
                        "down": ("540", "600", "540", "1600"),
                        "left": ("900", "1000", "100", "1000"),
                        "right": ("100", "1000", "900", "1000")
                    }
                    if direction in dirs:
                        x1, y1, x2, y2 = dirs[direction]
                        run_adb_raw(["shell", "input", "swipe", x1, y1, x2, y2, "300"], serial=get_active_serial())
                        console.print(f"[bold bright_green][✓] Gesture event executed: SWIPE_{direction.upper()}[/]")
                    else:
                        console.print("[red][!] Hướng vuốt không hợp lệ: up, down, left, right[/]")

            elif cmd == "type":
                if not args:
                    console.print("[red][!] Cú pháp: type <chuỗi văn bản>[/]")
                else:
                    text_input = " ".join(args)
                    send_text(get_active_serial() or "", text_input)
                    console.print(f"[bold bright_green][✓] Dispatched text input: {text_input}[/]")

            elif cmd == "key":
                if not args:
                    console.print("[red][!] Cú pháp: key <home|back|recents|power|volup|voldown>[/]")
                else:
                    keymap = {
                        "home": "3",
                        "back": "4",
                        "recents": "187",
                        "appswitch": "187",
                        "power": "26",
                        "volup": "24",
                        "voldown": "25"
                    }
                    k = args[0].lower()
                    keycode = keymap.get(k, k)
                    send_keyevent(get_active_serial() or "", keycode)
                    console.print(f"[bold bright_green][✓] Hardware key event dispatched: KEY_{k.upper()} (Code {keycode})[/]")

            elif cmd in ["snap", "screenshot"]:
                filename = args[0] if args else f"screenshot_{int(time.time())}.png"
                with console.status(f"[bold cyan]CAPTURING SCREEN BUFFER TO {filename}..."):
                    ok = take_screenshot(get_active_serial() or "", filename)
                if ok:
                    console.print(f"[bold bright_green][✓] Screenshot saved to: {os.path.abspath(filename)}[/]")
                else:
                    console.print("[red][!] Failed to capture screenshot.[/]")

            elif cmd == "open":
                if not args:
                    console.print("[red][!] Cú pháp: open <package_name>[/]")
                else:
                    pkg = args[0]
                    shortcuts = {
                        "youtube": "com.google.android.youtube",
                        "camera": "com.android.camera",
                        "settings": "com.android.settings",
                        "chrome": "com.android.chrome",
                        "magisk": "com.topjohnwu.magisk",
                        "photos": "com.google.android.apps.photos",
                        "playstore": "com.android.vending"
                    }
                    pkg = shortcuts.get(pkg.lower(), pkg)
                    with console.status(f"[bold green]LAUNCHING APPLICATION INTENT: {pkg}...[/]"):
                        run_adb_raw(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], serial=get_active_serial())
                    console.print(f"[bold bright_green][✓] Application {pkg} launched successfully.[/]")

            elif cmd == "kill":
                if not args:
                    console.print("[red][!] Cú pháp: kill <package_name>[/]")
                else:
                    pkg = args[0]
                    run_adb_raw(["shell", "am", "force-stop", pkg], serial=get_active_serial())
                    console.print(f"[bold red][✓] Application process {pkg} terminated.[/]")

            elif cmd == "untether":
                console.print("[bold yellow][*] CONFIGURING WIRELESS TCP/IP ADB LINK...[/]")
                tele = get_device_telemetry()
                ip = tele.get("ip")
                if not ip or ip in ["127.0.0.1", "Unknown"]:
                    console.print("[red][!] Could not resolve device IP address. Ensure device is connected to local Wi-Fi.[/]")
                else:
                    ok, msg = switch_to_wifi(get_active_serial() or "", ip, port=5555)
                    if ok:
                        console.print(f"[bold bright_green][✓] WIRELESS PROTOCOL ESTABLISHED: {msg}[/]")
                        console.print("[bold bright_cyan][+] Anh có thể rút dây cáp USB ra ngay bây giờ! Máy tính vẫn điều khiển điện thoại qua Wi-Fi 100%.[/]")
                    else:
                        console.print(f"[red][!] Lỗi kết nối không dây: {msg}[/]")

            elif cmd == "reboot":
                mode = args[0].lower() if args else ""
                console.print(f"[bold yellow][*] Dispatching reboot signal (mode: {mode or 'normal'})...[/]")
                reboot(get_active_serial() or "", mode)

            elif cmd == "shell":
                if not args:
                    console.print("[red][!] Cú pháp: shell <lệnh linux>[/]")
                else:
                    _, out, err = run_adb_raw(["shell"] + args, serial=get_active_serial())
                    console.print(Panel(out or err or "[dim italic]No output returned[/]", border_style="cyan", title="SHELL OUTPUT"))

            else:
                console.print(f"[red][!] Lệnh không nhận dạng được: '{cmd}'. Gõ 'clear' để xem danh sách lệnh.[/]")

        except KeyboardInterrupt:
            console.print("\n[yellow][!] Operation cancelled by user. Type 'exit' to quit.[/]")
        except Exception as e:
            console.print(f"[red][!] Exception: {e}[/]")

if __name__ == "__main__":
    main_loop()
