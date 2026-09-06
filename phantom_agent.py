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


class PhantomBotRunner:
    """
    Automated Humanized Flow Macro Runner.
    Supports in-app lifecycle management, cooperative cancellation (Emergency Stop),
    and custom log callbacks for GUI / HUD integration.
    """
    def __init__(self):
        self._is_cancelled = False
        self.stream_proc = None

    def cancel(self):
        """Signal the runner to abort workflow immediately."""
        self._is_cancelled = True

    @staticmethod
    def _emit_log(msg: str, log_callback=None):
        clean_msg = re.sub(r'\[/?[a-zA-Z0-9_ =#]+\]', '', msg)
        if callable(log_callback):
            try:
                log_callback(clean_msg)
            except Exception:
                pass
        if log_callback is None:
            try:
                console.print(msg)
            except Exception:
                print(clean_msg)

    def run_workflow(
        self,
        serial: str = "",
        log_callback=None,
        is_cancelled=None,
        launch_stream: bool = False
    ) -> bool:
        """
        Execute the 3-phase humanized workflow (Facebook -> Chrome Tinhte -> Nekogram).

        Args:
            serial: Target Android device serial.
            log_callback: Optional callable(str) for real-time progress logging.
            is_cancelled: Optional callable() -> bool for cooperative cancellation.
            launch_stream: If True, spawns an external scrcpy preview window.

        Returns:
            bool: True if completed fully, False if cancelled or aborted.
        """
        self._is_cancelled = False
        target_serial = resolve_serial(serial)
        if not target_serial:
            self._emit_log("❌ Không tìm thấy thiết bị Android nào để chạy Bot.", log_callback)
            return False

        def check_cancelled() -> bool:
            if self._is_cancelled:
                return True
            if callable(is_cancelled):
                try:
                    return bool(is_cancelled())
                except Exception:
                    return False
            return False

        def interruptible_sleep(seconds: float) -> bool:
            end_time = time.time() + seconds
            while time.time() < end_time:
                if check_cancelled():
                    return False
                rem = end_time - time.time()
                time.sleep(min(0.1, max(0.01, rem)))
            return True

        def handle_abort(phase_name: str = "") -> bool:
            phase_info = f" tại [{phase_name}]" if phase_name else ""
            self._emit_log(f"⏹️ [EMERGENCY STOP] Đã dừng Bot khẩn cấp{phase_info}.", log_callback)
            try:
                send_keyevent(target_serial, "3")  # Press Home
            except Exception:
                pass
            return False

        try:
            screen_size = get_screen_resolution(target_serial)
            device_info = {}
            try:
                device_info = get_device_info(target_serial)
            except Exception:
                pass

            if launch_stream:
                self.stream_proc = launch_scrcpy_stream(target_serial)

            if log_callback is None:
                print_mission_header(target_serial, screen_size, device_info)
            else:
                self._emit_log(f"🤖 Bắt đầu chu trình PhantomBot trên [{target_serial}] ({screen_size[0]}x{screen_size[1]})...", log_callback)

            # Step 0: Warmup
            if check_cancelled():
                return handle_abort("Khởi động")

            send_keyevent(target_serial, "224")                                    # Wakeup
            run_adb_raw(["shell", "wm", "dismiss-keyguard"], serial=target_serial) # Unlock
            send_keyevent(target_serial, "3")                                      # Home

            if not interruptible_sleep(1.5):
                return handle_abort("Khởi động")

            total_mission_start = time.time()

            # PHASE 1: FACEBOOK (~20s)
            self._emit_log("▶ [1/3] TARGET: FACEBOOK (com.facebook.katana) - Lướt News Feed...", log_callback)
            run_adb_raw(["shell", "monkey", "-p", APP_FACEBOOK, "-c", "android.intent.category.LAUNCHER", "1"], serial=target_serial)

            if not interruptible_sleep(3.5):
                return handle_abort("Facebook (Load)")

            fb_start = time.time()
            fb_duration = 20.0
            fb_swipes = 0

            if log_callback is None:
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
                        if check_cancelled():
                            return handle_abort("Facebook")
                        elapsed = time.time() - fb_start
                        progress.update(task_fb, completed=min(elapsed, fb_duration))

                        swipe_type = "down"
                        if fb_swipes > 1 and random.random() < 0.25:
                            swipe_type = "up"
                        elif random.random() < 0.15:
                            swipe_type = "flick"

                        human_swipe(swipe_type, screen_size=screen_size, serial=target_serial)
                        fb_swipes += 1

                        pause_time = random.uniform(2.2, 3.8)
                        if not interruptible_sleep(pause_time):
                            return handle_abort("Facebook")
            else:
                while (time.time() - fb_start) < fb_duration:
                    if check_cancelled():
                        return handle_abort("Facebook")

                    swipe_type = "down"
                    if fb_swipes > 1 and random.random() < 0.25:
                        swipe_type = "up"
                    elif random.random() < 0.15:
                        swipe_type = "flick"

                    human_swipe(swipe_type, screen_size=screen_size, serial=target_serial)
                    fb_swipes += 1

                    pause_time = random.uniform(2.2, 3.8)
                    if not interruptible_sleep(pause_time):
                        return handle_abort("Facebook")

            self._emit_log(f"✓ Facebook flow hoàn thành ({fb_swipes} lượt cuộn).", log_callback)

            if check_cancelled():
                return handle_abort("Chuyển tiếp")

            # PHASE 2: TECH NEWS VIA CHROME (~20s)
            self._emit_log(f"▶ [2/3] TARGET: Tech News ({TECH_URL}) qua Chrome...", log_callback)
            run_adb_raw(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", TECH_URL, APP_CHROME], serial=target_serial)

            if not interruptible_sleep(4.0):
                return handle_abort("Chrome (Load)")

            chrome_start = time.time()
            chrome_duration = 20.0
            chrome_swipes = 0

            if log_callback is None:
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
                        if check_cancelled():
                            return handle_abort("Chrome")
                        elapsed = time.time() - chrome_start
                        progress.update(task_chrome, completed=min(elapsed, chrome_duration))

                        swipe_type = "down"
                        if chrome_swipes > 2 and random.random() < 0.2:
                            swipe_type = "up"

                        human_swipe(swipe_type, screen_size=screen_size, serial=target_serial)
                        chrome_swipes += 1

                        pause_time = random.uniform(2.4, 4.0)
                        if not interruptible_sleep(pause_time):
                            return handle_abort("Chrome")
            else:
                while (time.time() - chrome_start) < chrome_duration:
                    if check_cancelled():
                        return handle_abort("Chrome")

                    swipe_type = "down"
                    if chrome_swipes > 2 and random.random() < 0.2:
                        swipe_type = "up"

                    human_swipe(swipe_type, screen_size=screen_size, serial=target_serial)
                    chrome_swipes += 1

                    pause_time = random.uniform(2.4, 4.0)
                    if not interruptible_sleep(pause_time):
                        return handle_abort("Chrome")

            self._emit_log(f"✓ Tech news flow hoàn thành ({chrome_swipes} lượt duyệt bài).", log_callback)

            if check_cancelled():
                return handle_abort("Chuyển tiếp")

            # PHASE 3: NEKOGRAM (~20s)
            self._emit_log("▶ [3/3] TARGET: Messenger Patrol [Nekogram] (tw.nekomimi.nekogram)...", log_callback)
            run_adb_raw(["shell", "monkey", "-p", APP_NEKOGRAM, "-c", "android.intent.category.LAUNCHER", "1"], serial=target_serial)

            if not interruptible_sleep(3.0):
                return handle_abort("Nekogram (Load)")

            neko_start = time.time()
            neko_duration = 20.0
            neko_swipes = 0

            if log_callback is None:
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
                        if check_cancelled():
                            return handle_abort("Nekogram")
                        elapsed = time.time() - neko_start
                        progress.update(task_neko, completed=min(elapsed, neko_duration))

                        human_swipe("down", screen_size=screen_size, serial=target_serial)
                        neko_swipes += 1

                        pause_time = random.uniform(2.0, 3.5)
                        if not interruptible_sleep(pause_time):
                            return handle_abort("Nekogram")
            else:
                while (time.time() - neko_start) < neko_duration:
                    if check_cancelled():
                        return handle_abort("Nekogram")

                    human_swipe("down", screen_size=screen_size, serial=target_serial)
                    neko_swipes += 1

                    pause_time = random.uniform(2.0, 3.5)
                    if not interruptible_sleep(pause_time):
                        return handle_abort("Nekogram")

            self._emit_log(f"✓ Nekogram channel patrol hoàn thành ({neko_swipes} lượt cuộn).", log_callback)

            # PHASE 4: CLEANUP & RETURN TO SECURE LAUNCHER
            if check_cancelled():
                return handle_abort("Cleanup")

            self._emit_log("🏠 Hoàn thành kịch bản. Trở về màn hình chính (Home)...", log_callback)
            send_keyevent(target_serial, "3")
            interruptible_sleep(1.0)

            total_time = time.time() - total_mission_start
            self._emit_log(f"🎉 Toàn bộ chu trình PhantomBot đã kết thúc thành công trong {total_time:.1f} giây!", log_callback)

            if log_callback is None:
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

            return True

        except Exception as e:
            self._emit_log(f"❌ Ngoại lệ trong quá trình thực thi PhantomBot: {e}", log_callback)
            try:
                send_keyevent(target_serial, "3")
            except Exception:
                pass
            return False


def main():
    serial = resolve_serial()
    runner = PhantomBotRunner()
    runner.run_workflow(serial, launch_stream=True)


if __name__ == "__main__":
    _serial = resolve_serial()
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red][!] FLOW ABORTED BY USER OVERRIDE.[/]")
        if _serial:
            send_keyevent(_serial, "3")
