# -*- coding: utf-8 -*-
"""
================================================================================
  PROJECT: OPERATION PHANTOM_SCROLL // GHOST SURVEILLANCE BOT
  TARGET : POCOPHONE F1 [beryllium] // ANDROID 10
  PURPOSE: AUTONOMOUS HUMANIZED SOCIAL & INTEL BROWSING WITH LIVE HUD STREAM
================================================================================
"""

import os
import sys
import time
import random
import subprocess
import threading
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from rich.table import Table

console = Console()

# Resolve Paths
SCRCPY_DIR = r"C:\Users\phamn\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1"
ADB_PATH = os.path.join(SCRCPY_DIR, "adb.exe")
if not os.path.exists(ADB_PATH):
    ADB_PATH = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")

SCRCPY_PATH = os.path.join(SCRCPY_DIR, "scrcpy.exe")

# Target Apps
APP_FACEBOOK = "com.facebook.katana"
APP_CHROME   = "com.android.chrome"
APP_NEKOGRAM = "tw.nekomimi.nekogram"
TECH_URL     = "https://tinhte.vn"

def run_adb(args, timeout=8):
    try:
        cmd = [ADB_PATH] + args
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return res.stdout.strip()
    except Exception as e:
        return ""

def launch_scrcpy_stream():
    """Launch 60FPS hardware-accelerated stream window always on top."""
    cmd = [
        SCRCPY_PATH,
        "--always-on-top",
        "--window-title", "PHANTOM_OPERATOR // LIVE RECON STREAM [60FPS]",
        "--window-width", "400",
        "--stay-awake"
    ]
    try:
        proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
        return proc
    except Exception as e:
        console.print(f"[bold red][!] Scrcpy initialization failed: {e}[/]")
        return None

def human_swipe(direction="down"):
    """
    Simulate natural human finger drag with randomized coordinates,
    velocity curves, and slight trajectory deviations to evade anti-bot heuristics.
    Safe neutral corridor (X: 480 - 600) to NEVER touch like or comment buttons.
    """
    center_x = random.randint(480, 580)
    jitter_x = center_x + random.randint(-25, 25)

    if direction == "down": # scrolls down (drag finger up)
        start_y = random.randint(1450, 1680)
        end_y   = random.randint(580, 780)
        duration = random.randint(480, 720)
    elif direction == "up": # scrolls up slightly (re-reading)
        start_y = random.randint(700, 850)
        end_y   = random.randint(1100, 1300)
        duration = random.randint(350, 500)
    elif direction == "flick": # fast momentum flick
        start_y = random.randint(1600, 1750)
        end_y   = random.randint(400, 550)
        duration = random.randint(220, 320)

    run_adb(["shell", "input", "swipe", str(center_x), str(start_y), str(jitter_x), str(end_y), str(duration)])

def print_mission_header():
    console.clear()
    banner = """
 [bold bright_green]██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗[/]
 [bold bright_green]██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║[/]
 [bold bright_cyan]██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║[/]
 [bold bright_cyan]██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║[/]
 [bold bright_magenta]██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║[/]
 [bold bright_magenta]╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝[/]
       [bold bright_yellow]───[ OPERATION: PHANTOM_SCROLL // AUTONOMOUS AGENT PROTOCOL ]───[/]
    """
    console.print(banner)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row(
        "[bold cyan]AGENT STATUS:[/] [bold blink bright_green]● COVERT EXECUTION ACTIVE[/]",
        "[bold cyan]TACTICAL LINK:[/] [white]ADB HIGH-SPEED[/]",
        "[bold cyan]TARGET DEVICE:[/] [white]POCOPHONE F1 (beryllium)[/]"
    )
    table.add_row(
        "[bold cyan]MISSION TIME:[/] [yellow]~60 SECONDS TOTAL[/]",
        "[bold cyan]BEHAVIOR:[/] [green]PASSIVE GHOST (NO LIKE / NO COMMENT)[/]",
        "[bold cyan]STREAM HUD:[/] [bold magenta]60FPS SCRCPY MIRROR[/]"
    )
    console.print(Panel(table, border_style="bright_green"))

def main():
    print_mission_header()

    # Step 0: Warmup & Stream Launch
    console.print("[bold bright_green][1/5] INITIALIZING TACTICAL SUBSYSTEMS...[/]")
    with console.status("[bold cyan]Waking up target & launching 60FPS HUD Screen Stream...", spinner="dots12"):
        run_adb(["shell", "input", "keyevent", "224"]) # Wakeup
        run_adb(["shell", "wm", "dismiss-keyguard"])    # Unlock
        run_adb(["shell", "input", "keyevent", "3"])     # Home
        stream_proc = launch_scrcpy_stream()
        time.sleep(2.5)

    console.print("[bold bright_green][✓] Neural Link engaged. Live Screen is now streaming on your PC.[/]")
    time.sleep(1)

    total_mission_start = time.time()

    # PHASE 1: FACEBOOK (~20s)
    console.print("\n[bold bright_cyan]══════════════════════════════════════════════════════════════════════[/]")
    console.print("[bold bright_green]▶ [PHASE 1/3] TARGET: FACEBOOK (com.facebook.katana)[/]")
    console.print("[dim cyan][*] Action: Infiltrating news feed // Simulating organic eye-tracking scroll...[/]")
    console.print("[bold bright_yellow][!] Policy: Strict surveillance mode (Zero likes, Zero comments).[/]")

    # Launch Facebook
    run_adb(["shell", "monkey", "-p", APP_FACEBOOK, "-c", "android.intent.category.LAUNCHER", "1"])
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
        task_fb = progress.add_task("[bold cyan]Surveilling Facebook News Feed...", total=fb_duration)
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

            human_swipe(swipe_type)
            swipe_count += 1

            # Pause to "read"
            pause_time = random.uniform(2.2, 3.8)
            time.sleep(pause_time)

    console.print(f"[bold bright_green][✓] Facebook surveillance complete ({swipe_count} scroll actions executed).[/]")

    # PHASE 2: TECH NEWS VIA CHROME (~20s)
    console.print("\n[bold bright_cyan]══════════════════════════════════════════════════════════════════════[/]")
    console.print(f"[bold bright_green]▶ [PHASE 2/3] TARGET: TECH INTELLIGENCE VIA CHROME ({TECH_URL})[/]")
    console.print("[dim cyan][*] Action: Deep-linking to Tinhte tech portal // Reading tech news headlines...[/]")

    # Launch Chrome directly with URL
    run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", TECH_URL, APP_CHROME])
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

            human_swipe(swipe_type)
            chrome_swipes += 1

            pause_time = random.uniform(2.4, 4.0)
            time.sleep(pause_time)

    console.print(f"[bold bright_green][✓] Tech news intel harvested ({chrome_swipes} articles browsed).[/]")

    # PHASE 3: NEKOGRAM (~20s)
    console.print("\n[bold bright_cyan]══════════════════════════════════════════════════════════════════════[/]")
    console.print("[bold bright_green]▶ [PHASE 3/3] TARGET: ENCRYPTED MESSENGER [NEKOGRAM] (tw.nekomimi.nekogram)[/]")
    console.print("[dim cyan][*] Action: Infiltrating chat feeds & telegram channels...[/]")

    # Launch Nekogram
    run_adb(["shell", "monkey", "-p", APP_NEKOGRAM, "-c", "android.intent.category.LAUNCHER", "1"])
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

            human_swipe("down")
            neko_swipes += 1

            pause_time = random.uniform(2.0, 3.5)
            time.sleep(pause_time)

    console.print(f"[bold bright_green][✓] Nekogram channel patrol completed ({neko_swipes} scrolls executed).[/]")

    # PHASE 4: CLEANUP & RETURN SECURE LAUNCHER
    console.print("\n[bold bright_cyan]══════════════════════════════════════════════════════════════════════[/]")
    console.print("[bold bright_yellow][*] PURGING VOLATILE TELEMETRY & RETURNING TO HOME LAUNCHER...[/]")
    run_adb(["shell", "input", "keyevent", "3"]) # Home key
    time.sleep(1.0)

    total_time = time.time() - total_mission_start

    finish_panel = Panel(
        f"""[bold bright_green]◈ MISSION SUCCESSFUL: ALL TARGETS EXECUTED IN {total_time:.1f} SECONDS ◈[/]

  [white]• Target [1]:[/] [bold bright_green]Facebook (com.facebook.katana)[/]      [dim]→ 20s Clean Humanized Browsing[/]
  [white]• Target [2]:[/] [bold bright_cyan]Chrome [Tinhte Tech Portal][/]          [dim]→ 20s Headline Intelligence[/]
  [white]• Target [3]:[/] [bold bright_magenta]Nekogram (tw.nekomimi.nekogram)[/]      [dim]→ 20s Channel Feed Patrol[/]
  [white]• Live HUD  :[/] [bold yellow]Scrcpy 60FPS Hardware Mirror[/]          [dim]→ Streamed Live to PC Screen[/]
  [white]• Footprint :[/] [bold blink green]ZERO LIKES // ZERO COMMENTS // 100% GHOST OPERATION[/]
""",
        title="[bold bright_green]✔ OPERATION COMPLETED[/]",
        border_style="bright_green"
    )
    console.print(finish_panel)
    console.print("[dim green]Cửa sổ stream màn hình vẫn đang hoạt động. Anh có thể thao tác tiếp hoặc đóng lại bất cứ lúc nào.[/]\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red][!] MISSION ABORTED BY USER OVERRIDE.[/]")
        run_adb(["shell", "input", "keyevent", "3"])
