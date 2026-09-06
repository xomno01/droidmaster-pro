# -*- coding: utf-8 -*-
"""
================================================================================
  PROJECT: OPERATION PHANTOM_SCROLL // HUMANIZED FLOW MACRO
  PURPOSE: HUMANIZED SMART MACRO / FLOW AUTOMATION WITH LIVE HUD STREAM
================================================================================
"""

import os
import re
import sys
import time
import random
import subprocess
import threading
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from rich.table import Table

from adb_core import (
    run_adb_raw,
    send_keyevent,
    launch_scrcpy,
    BIN_DIR,
    ADB_PATH,
    get_device_info,
)

console = Console()

# Target Apps & URLs
APP_FACEBOOK = "com.facebook.katana"
APP_CHROME   = "com.android.chrome"
APP_NEKOGRAM = "tw.nekomimi.nekogram"
TECH_URL     = "https://tinhte.vn"


def resolve_serial(target_serial: Optional[str] = None) -> str:
    """Dynamically discover or validate connected device serial."""
    if target_serial:
        return target_serial
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        return sys.argv[1]

    # Check via adb get-serialno
    code, stdout, _ = run_adb_raw(["get-serialno"])
    if code == 0 and stdout and stdout != "unknown":
        return stdout

    # Check via adb devices
    code, stdout, _ = run_adb_raw(["devices"])
    if code == 0 and stdout:
        for line in stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("*") or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                return parts[0]
    return ""


def get_screen_resolution(serial: Optional[str] = None) -> Tuple[int, int]:
    """
    Fetch screen resolution dynamically from get_device_info(serial) or wm size.
    Returns (width, height) tuple.
    """
    if serial:
        try:
            info = get_device_info(serial)
            res_str = info.get("resolution", "")
            if "x" in res_str:
                parts = res_str.split("x")
                return int(parts[0]), int(parts[1])
        except Exception:
            pass

    # Direct fallback via wm size
    code, stdout, _ = run_adb_raw(["shell", "wm", "size"], serial=serial)
    if code == 0 and stdout:
        match = re.search(r"Physical size:\s*(\d+)\s*x\s*(\d+)", stdout)
        if not match:
            match = re.search(r"(\d+)\s*x\s*(\d+)", stdout)
        if match:
            return int(match.group(1)), int(match.group(2))

    return 1080, 2240  # Safe generic fallback


def run_adb(args, timeout=8, serial: Optional[str] = None) -> str:
    """Execute raw adb command via adb_core and return trimmed stdout."""
    code, stdout, _ = run_adb_raw(args, timeout=timeout, serial=serial)
    return stdout if code == 0 else ""


def launch_scrcpy_stream(serial: str = "") -> Optional[subprocess.Popen]:
    """Launch hardware-accelerated scrcpy mirror window always on top."""
    if not serial:
        serial = resolve_serial()
    options = {
        "always_on_top": True,
        "stay_awake": True,
        "title": f"PHANTOM_OPERATOR // LIVE STREAM HUD [{'active' if serial else 'auto'}]",
        "max_size": 0,
        "bitrate": "8M"
    }
    try:
        proc = launch_scrcpy(serial=serial, options=options)
        return proc
    except Exception as e:
        console.print(f"[bold red][!] Scrcpy initialization failed: {e}[/]")
        return None

def human_swipe(
    direction: str = "down",
    screen_size: Tuple[int, int] = (1080, 2240),
    serial: Optional[str] = None
):
    """
    Simulate natural human finger drag with randomized coordinates,
    velocity curves, and slight trajectory deviations to evade anti-bot heuristics.
    Coordinates are calculated proportionally (e.g. 20% to 80% of screen dimensions)
    with a safe neutral corridor (45% - 55% width) to avoid like and comment buttons.
    """
    width, height = screen_size

    # Neutral central corridor (45% - 55% of screen width)
    min_x = int(width * 0.45)
    max_x = int(width * 0.55)
    center_x = random.randint(min_x, max_x)
    jitter_max = max(10, int(width * 0.025))
    jitter_x = center_x + random.randint(-jitter_max, jitter_max)

    if direction == "down":  # scrolls down (drag finger up: ~65-75% to ~25-35% height)
        start_y = random.randint(int(height * 0.65), int(height * 0.75))
        end_y = random.randint(int(height * 0.25), int(height * 0.35))
        duration = random.randint(480, 720)
    elif direction == "up":  # scrolls up slightly (re-reading: ~30-38% to ~50-60% height)
        start_y = random.randint(int(height * 0.30), int(height * 0.38))
        end_y = random.randint(int(height * 0.50), int(height * 0.60))
        duration = random.randint(350, 500)
    elif direction == "flick":  # fast momentum flick (~70-80% to ~18-25% height)
        start_y = random.randint(int(height * 0.70), int(height * 0.80))
        end_y = random.randint(int(height * 0.18), int(height * 0.25))
        duration = random.randint(220, 320)
    else:
        start_y = random.randint(int(height * 0.60), int(height * 0.70))
        end_y = random.randint(int(height * 0.30), int(height * 0.40))
        duration = random.randint(400, 600)

    run_adb_raw(
        ["shell", "input", "swipe", str(center_x), str(start_y), str(jitter_x), str(end_y), str(duration)],
        serial=serial
    )


def print_mission_header(serial: str = "", screen_size: Tuple[int, int] = (1080, 2240), device_info: Optional[dict] = None):
    console.clear()
    banner = """
 [bold bright_green]██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗[/]
 [bold bright_green]██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║[/]
 [bold bright_cyan]██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║[/]
 [bold bright_cyan]██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║[/]
 [bold bright_magenta]██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║[/]
 [bold bright_magenta]╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝[/]
     [bold bright_yellow]───[ OPERATION: PHANTOM_SCROLL // HUMANIZED SMART MACRO / FLOW AUTOMATION ]───[/]
    """
    console.print(banner)

    dev_name = "Android Device"
    if device_info:
        model = device_info.get("model", "")
        brand = device_info.get("brand", "")
        if model and model != "Unknown":
            dev_name = f"{brand} {model}".strip()

    serial_display = serial if serial else "Auto-detected"
    res_display = f"{screen_size[0]}x{screen_size[1]}"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row(
        "[bold cyan]FLOW STATUS:[/] [bold blink bright_green]● SMART MACRO ACTIVE[/]",
        f"[bold cyan]TACTICAL LINK:[/] [white]ADB ({os.path.basename(ADB_PATH)})[/]",
        f"[bold cyan]TARGET DEVICE:[/] [white]{dev_name} [{serial_display}][/]"
    )
    table.add_row(
        "[bold cyan]MISSION TIME:[/] [yellow]~60 SECONDS TOTAL[/]",
        "[bold cyan]BEHAVIOR:[/] [green]PASSIVE GHOST (NO LIKE / NO COMMENT)[/]",
        f"[bold cyan]RESOLUTION:[/] [bold magenta]{res_display}[/]"
    )
    console.print(Panel(table, border_style="bright_green"))


def main():
    serial = resolve_serial()
    screen_size = get_screen_resolution(serial)
    device_info = {}
    if serial:
        try:
            device_info = get_device_info(serial)
        except Exception:
            pass

    print_mission_header(serial, screen_size, device_info)

    # Step 0: Warmup & Stream Launch
    console.print("[bold bright_green][1/5] INITIALIZING TACTICAL SUBSYSTEMS...[/]")
    with console.status("[bold cyan]Waking up target & launching Screen Stream HUD...", spinner="dots12"):
        send_keyevent(serial, "224")                                    # Wakeup
        run_adb_raw(["shell", "wm", "dismiss-keyguard"], serial=serial) # Unlock
        send_keyevent(serial, "3")                                      # Home
        stream_proc = launch_scrcpy_stream(serial)
        time.sleep(2.5)

    console.print("[bold bright_green][✓] Scrcpy stream engaged. Live Screen is now streaming on your PC.[/]")
    time.sleep(1)

    total_mission_start = time.time()

    # PHASE 1: FACEBOOK (~20s)
    console.print("\n[bold bright_cyan]══════════════════════════════════════════════════════════════════════[/]")
    console.print("[bold bright_green]▶ [PHASE 1/3] TARGET: FACEBOOK (com.facebook.katana)[/]")
    console.print("[dim cyan][*] Action: Infiltrating news feed // Simulating humanized reading scroll...[/]")
    console.print("[bold bright_yellow][!] Policy: Strict surveillance mode (Zero likes, Zero comments).[/]")

    # Launch Facebook
    run_adb_raw(["shell", "monkey", "-p", APP_FACEBOOK, "-c", "android.intent.category.LAUNCHER", "1"], serial=serial)
    time.sleep(3.5) # Wait for feed to load

    fb_start = time.time()
    fb_duration = 20.0
    swipe_count = 0

    with Progress(
        SpinnerColumn(spinner_name="line", style="bold green"),
        TextColumn("[bold bright_green]{task.description}"),
        BarColumn(bar_width=35, style="green", complete_style="bold bright_green"),
        TextColumn("[bold cyan]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_fb = progress.add_task("[bold cyan]Executing Facebook News Feed Flow...", total=fb_duration)
        while (time.time() - fb_start) < fb_duration:
            elapsed = time.time() - fb_start
            progress.update(task_fb, completed=min(elapsed, fb_duration))

            # Decide swipe action
            swipe_type = "down"
            if swipe_count > 1 and random.random() < 0.25:
                # 25% chance of slight micro-backscroll (human reading behavior)
                swipe_type = "up"
            elif random.random() < 0.15:
                swipe_type = "flick"

            human_swipe(swipe_type, screen_size=screen_size, serial=serial)
            swipe_count += 1

            # Pause to "read"
            pause_time = random.uniform(2.2, 3.8)
            time.sleep(pause_time)

    console.print(f"[bold bright_green][✓] Facebook flow complete ({swipe_count} scroll actions executed).[/]")

    # PHASE 2: TECH NEWS VIA CHROME (~20s)
    console.print("\n[bold bright_cyan]══════════════════════════════════════════════════════════════════════[/]")
    console.print(f"[bold bright_green]▶ [PHASE 2/3] TARGET: TECH NEWS AUTOMATION VIA CHROME ({TECH_URL})[/]")
    console.print("[dim cyan][*] Action: Deep-linking to Tinhte tech portal // Reading tech news headlines...[/]")

    # Launch Chrome directly with URL
    run_adb_raw(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", TECH_URL, APP_CHROME], serial=serial)
    time.sleep(4.0) # Wait for page load

    chrome_start = time.time()
    chrome_duration = 20.0
    chrome_swipes = 0

    with Progress(
        SpinnerColumn(spinner_name="line", style="bold cyan"),
        TextColumn("[bold bright_cyan]{task.description}"),
        BarColumn(bar_width=35, style="cyan", complete_style="bold bright_cyan"),
        TextColumn("[bold cyan]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_chrome = progress.add_task("[bold bright_cyan]Reading Tech Articles & Trends...", total=chrome_duration)
        while (time.time() - chrome_start) < chrome_duration:
            elapsed = time.time() - chrome_start
            progress.update(task_chrome, completed=min(elapsed, chrome_duration))

            swipe_type = "down"
            if chrome_swipes > 2 and random.random() < 0.2:
                swipe_type = "up" # Re-read headline

            human_swipe(swipe_type, screen_size=screen_size, serial=serial)
            chrome_swipes += 1

            pause_time = random.uniform(2.4, 4.0)
            time.sleep(pause_time)

    console.print(f"[bold bright_green][✓] Tech news browsing completed ({chrome_swipes} articles browsed).[/]")

    # PHASE 3: NEKOGRAM (~20s)
    console.print("\n[bold bright_cyan]══════════════════════════════════════════════════════════════════════[/]")
    console.print("[bold bright_green]▶ [PHASE 3/3] TARGET: MESSENGER PATROL [NEKOGRAM] (tw.nekomimi.nekogram)[/]")
    console.print("[dim cyan][*] Action: Browsing chat feeds & telegram channels...[/]")

    # Launch Nekogram
    run_adb_raw(["shell", "monkey", "-p", APP_NEKOGRAM, "-c", "android.intent.category.LAUNCHER", "1"], serial=serial)
    time.sleep(3.0)

    neko_start = time.time()
    neko_duration = 20.0
    neko_swipes = 0

    with Progress(
        SpinnerColumn(spinner_name="line", style="bold magenta"),
        TextColumn("[bold bright_magenta]{task.description}"),
        BarColumn(bar_width=35, style="magenta", complete_style="bold bright_magenta"),
        TextColumn("[bold cyan]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_neko = progress.add_task("[bold bright_magenta]Browsing Nekogram Channels & Chats...", total=neko_duration)
        while (time.time() - neko_start) < neko_duration:
            elapsed = time.time() - neko_start
            progress.update(task_neko, completed=min(elapsed, neko_duration))

            human_swipe("down", screen_size=screen_size, serial=serial)
            neko_swipes += 1

            pause_time = random.uniform(2.0, 3.5)
            time.sleep(pause_time)

    console.print(f"[bold bright_green][✓] Nekogram channel patrol completed ({neko_swipes} scrolls executed).[/]")

    # PHASE 4: CLEANUP & RETURN SECURE LAUNCHER
    console.print("\n[bold bright_cyan]══════════════════════════════════════════════════════════════════════[/]")
    console.print("[bold bright_yellow][*] RETURNING TO HOME LAUNCHER...[/]")
    send_keyevent(serial, "3") # Home key
    time.sleep(1.0)

    total_time = time.time() - total_mission_start

    finish_panel = Panel(
        f"""[bold bright_green]◈ FLOW EXECUTION COMPLETED: ALL TARGETS PROCESSED IN {total_time:.1f} SECONDS ◈[/]

  [white]• Target [1]:[/] [bold bright_green]Facebook (com.facebook.katana)[/]      [dim]→ 20s Clean Humanized Browsing[/]
  [white]• Target [2]:[/] [bold bright_cyan]Chrome [Tinhte Tech Portal][/]          [dim]→ 20s Humanized News Flow[/]
  [white]• Target [3]:[/] [bold bright_magenta]Nekogram (tw.nekomimi.nekogram)[/]      [dim]→ 20s Channel Feed Flow[/]
  [white]• Live HUD  :[/] [bold yellow]Scrcpy Hardware Mirror[/]                [dim]→ Streamed Live to PC Screen[/]
  [white]• Footprint :[/] [bold blink green]ZERO LIKES // ZERO COMMENTS // CLEAN AUTOMATION[/]
""",
        title="[bold bright_green]✔ OPERATION COMPLETED[/]",
        border_style="bright_green"
    )
    console.print(finish_panel)
    console.print("[dim green]Cửa sổ stream màn hình vẫn đang hoạt động. Anh có thể thao tác tiếp hoặc đóng lại bất cứ lúc nào.[/]\n")


if __name__ == "__main__":
    _serial = resolve_serial()
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red][!] FLOW ABORTED BY USER OVERRIDE.[/]")
        send_keyevent(_serial, "3")
