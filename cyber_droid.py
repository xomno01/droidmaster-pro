# -*- coding: utf-8 -*-
"""
CYBER_DROID C2 // POCOPHONE F1 REMOTE ACCESS & TACTICAL CONTROL SYSTEM
Author: Antigravity Cyber Division
Target: POCOPHONE F1 (beryllium) // Android 10
"""

import os
import sys
import time
import subprocess
import re
import random
import threading
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.text import Text

console = Console()

# Resolve ADB and Scrcpy Paths
SCRCPY_DIR = r"C:\Users\phamn\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1"
ADB_PATH = os.path.join(SCRCPY_DIR, "adb.exe")
if not os.path.exists(ADB_PATH):
    ADB_PATH = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")

SCRCPY_PATH = os.path.join(SCRCPY_DIR, "scrcpy.exe")

def run_adb(args, timeout=10, capture=True):
    cmd = [ADB_PATH] + args
    try:
        res = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return res.stdout.strip() if capture else ""
    except Exception as e:
        return f"ERR: {e}"

def hacker_init_sequence():
    console.clear()
    with Progress(
        SpinnerColumn(spinner_name="dots12", style="bold green"),
        TextColumn("[bold green]{task.description}"),
        BarColumn(bar_width=40, style="green", complete_style="bold bright_green"),
        TextColumn("[bold bright_cyan]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        t1 = progress.add_task("[bold cyan]INITIALIZING NEURAL ADB BRIDGE...", total=100)
        t2 = progress.add_task("[bold green]BYPASSING PERMISSION ENCLAVE...", total=100)
        t3 = progress.add_task("[bold magenta]ESTABLISHING C2 DOWNLINK TO POCOPHONE F1...", total=100)

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
               [bold yellow]───[ TACTICAL C2 INTERFACE // TARGET: BER-F1 // OS: ANDROID 10 ]───[/]
    """
    console.print(banner_text)

def get_device_telemetry():
    model = run_adb(["shell", "getprop", "ro.product.model"]) or "POCO F1"
    battery_info = run_adb(["shell", "dumpsys", "battery"])
    level_match = re.search(r"level:\s*(\d+)", battery_info)
    level = level_match.group(1) if level_match else "99"
    temp_match = re.search(r"temperature:\s*(\d+)", battery_info)
    temp = f"{int(temp_match.group(1))/10:.1f}°C" if temp_match else "41.0°C"

    ip_info = run_adb(["shell", "ip", "route"])
    ip_match = re.search(r"src\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", ip_info)
    ip_addr = ip_match.group(1) if ip_match else "192.168.0.106"

    focus_info = run_adb(["shell", "dumpsys", "window"])
    focus_match = re.search(r"mCurrentFocus=Window\{[^\s]+\s+[^\s]+\s+([^/\s]+)", focus_info)
    active_pkg = focus_match.group(1) if focus_match else "Launcher"

    return {
        "model": model,
        "battery": f"{level}%",
        "temp": temp,
        "ip": ip_addr,
        "active": active_pkg,
        "security": "MAGISK / SECURE_ADB_GRANTED"
    }

def print_hud():
    tele = get_device_telemetry()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row(
        f"[bold bright_green]TARGET:[/] [white]{tele['model']} (beryllium)[/]",
        f"[bold bright_cyan]NET IP:[/] [white]{tele['ip']}:5555[/]",
        f"[bold bright_yellow]POWER:[/] [white]{tele['battery']} ({tele['temp']})[/]"
    )
    table.add_row(
        f"[bold bright_magenta]EXPLOIT LEVEL:[/] [green]{tele['security']}[/]",
        f"[bold bright_cyan]FOCUS APPS:[/] [white]{tele['active']}[/]",
        f"[bold bright_green]STATUS:[/] [bold blink bright_green]● ARMED & LINKED[/]"
    )
    console.print(Panel(table, title="[bold bright_green]◈ TACTICAL TELEMETRY HUD ◈[/]", border_style="bright_green"))

def matrix_rain(duration=3):
    console.print("[bold green]INJECTING MATRIX CIPHER DATASTREAM...[/]")
    katakana = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ0123456789ABCDEF!@#$%^&*"
    width = console.width or 80
    end_time = time.time() + duration
    while time.time() < end_time:
        line = "".join(random.choice(katakana) if random.random() > 0.4 else " " for _ in range(width))
        style = random.choice(["bold green", "bright_green", "green", "white"])
        console.print(f"[{style}]{line}[/]")
        time.sleep(0.04)

def cmd_recon():
    with console.status("[bold cyan]SCANNING TARGET UI HIERARCHY TREE...", spinner="bouncingBar"):
        run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
        xml_content = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])
        run_adb(["shell", "rm", "/sdcard/window_dump.xml"])

    nodes = re.findall(r'<node [^>]*text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_content)
    
    table = Table(title="[bold bright_green]◈ DISCOVERED RECON TARGETS & COORDINATES ◈[/]", border_style="cyan")
    table.add_column("Index", style="dim cyan", justify="right")
    table.add_column("Element Label / Text", style="bold white")
    table.add_column("Center Coordinate (X, Y)", style="bold bright_yellow")
    table.add_column("Quick Command", style="bold bright_green")

    count = 0
    for text, x1, y1, x2, y2 in nodes:
        if not text.strip():
            continue
        cx = (int(x1) + int(x2)) // 2
        cy = (int(y1) + int(y2)) // 2
        count += 1
        table.add_row(str(count), text, f"({cx}, {cy})", f"tap {cx} {cy}")
        if count >= 15:
            break

    if count > 0:
        console.print(table)
    else:
        console.print("[yellow][!] No direct text elements detected or home launcher in icon-only mode.[/]")

def cmd_scrcpy():
    console.print("[bold bright_green][+] DEPLOYING ZERO-LATENCY 60FPS SCREEN MIRROR (ALWAYS ON TOP)...[/]")
    cmd = [
        SCRCPY_PATH,
        "--always-on-top",
        "--window-title", "CYBER_LINK // POCOPHONE F1 (BER-F1)",
        "--window-width", "400",
        "--stay-awake"
    ]
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
    console.print("[bold cyan][*] Screen Mirror active! Direct mouse click and keyboard input are synced to phone.[/]")

def cmd_apps():
    with console.status("[bold cyan]HARVESTING 3RD PARTY PACKAGES...", spinner="dots"):
        raw = run_adb(["shell", "pm", "list", "packages", "-3"])
    packages = [line.replace("package:", "").strip() for line in raw.splitlines() if line.strip()]
    
    table = Table(title="[bold bright_cyan]◈ TARGET APPLICATION REGISTRY (3RD-PARTY) ◈[/]", border_style="cyan")
    table.add_column("#", style="dim cyan", justify="right")
    table.add_column("Package Identifier", style="bold white")
    table.add_column("Execution Command", style="bold bright_green")

    for idx, pkg in enumerate(packages[:20], 1):
        table.add_row(str(idx), pkg, f"open {pkg}")

    console.print(table)

def main_loop():
    hacker_init_sequence()
    print_banner()
    print_hud()
    
    console.print("""
 [bold bright_cyan]AVAILABLE OPERATIONS:[/]
   [bold bright_green]recon[/]          : Quét toàn bộ nút bấm & toạ độ UI trên màn hình
   [bold bright_green]hud[/] / [bold bright_green]scrcpy[/]    : Bật màn hình điện thoại 60FPS Always-on-Top cạnh IDE (chuột + phím)
   [bold bright_green]tap <x> <y>[/]   : Bắn xung cảm ứng vào toạ độ (VD: tap 540 1000)
   [bold bright_green]swipe <dir>[/]   : Vuốt cảm ứng (up, down, left, right)
   [bold bright_green]type <text>[/]   : Bắn nội dung vào ô nhập liệu (VD: type Hello World)
   [bold bright_green]key <code/btn>[/]: Bấm phím (home, back, recents, power, volup, voldown)
   [bold bright_green]apps[/]           : Liệt kê các ứng dụng trên máy
   [bold bright_green]open <pkg>[/]     : Mở app (VD: open youtube, open camera)
   [bold bright_green]kill <pkg>[/]     : Buộc dừng ứng dụng
   [bold bright_green]untether[/]       : Rút dây USB và chuyển sang điều khiển không dây Wi-Fi!
   [bold bright_green]matrix[/]         : Hiệu ứng Matrix Data Rain
   [bold bright_green]shell <cmd>[/]    : Thực thi lệnh Linux Shell trực tiếp trên Android
   [bold bright_green]cls[/] / [bold bright_green]clear[/]    : Xoá màn hình & nạp lại HUD
   [bold bright_green]exit[/]           : Đóng phiên C2
    """)

    while True:
        try:
            cmd_line = console.input("[bold bright_green]root@beryllium[/][white]:[/][bold bright_cyan]~[/][bold yellow]#[/] ").strip()
            if not cmd_line:
                continue

            parts = cmd_line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ["exit", "quit", "q"]:
                console.print("[bold red][!] DISCONNECTING C2 LINK... SECURE CHANNELS PURGED.[/]")
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

            elif cmd == "apps":
                cmd_apps()

            elif cmd == "tap":
                if len(args) < 2:
                    console.print("[red][!] Cú pháp: tap <x> <y>[/]")
                else:
                    x, y = args[0], args[1]
                    with console.status(f"[bold green]INJECTING TACTILE PULSE AT ({x}, {y})...[/]"):
                        run_adb(["shell", "input", "tap", x, y])
                    console.print(f"[bold bright_green][✓] Target pulsed at ({x}, {y}) successfully.[/]")

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
                        run_adb(["shell", "input", "swipe", x1, y1, x2, y2, "300"])
                        console.print(f"[bold bright_green][✓] Kinetic vector executed: SWIPE_{direction.upper()}[/]")
                    else:
                        console.print("[red][!] Hướng vuốt không hợp lệ: up, down, left, right[/]")

            elif cmd == "type":
                if not args:
                    console.print("[red][!] Cú pháp: type <chuỗi văn bản>[/]")
                else:
                    payload = "%s".join(args) # adb input text requires %s for spaces
                    run_adb(["shell", "input", "text", payload])
                    console.print(f"[bold bright_green][✓] Injected payload: {' '.join(args)}[/]")

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
                    run_adb(["shell", "input", "keyevent", keycode])
                    console.print(f"[bold bright_green][✓] Hardware interrupt signal sent: KEY_{k.upper()} (Code {keycode})[/]")

            elif cmd == "open":
                if not args:
                    console.print("[red][!] Cú pháp: open <package_name>[/]")
                else:
                    pkg = args[0]
                    # Check popular shortcuts
                    shortcuts = {
                        "youtube": "com.google.android.youtube",
                        "camera": "com.android.camera",
                        "settings": "com.android.settings",
                        "chrome": "com.android.chrome",
                        "magisk": "com.topjohnwu.magisk"
                    }
                    pkg = shortcuts.get(pkg.lower(), pkg)
                    with console.status(f"[bold green]SPAWNING REMOTE PROCESS: {pkg}...[/]"):
                        run_adb(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
                    console.print(f"[bold bright_green][✓] Process {pkg} spawned successfully.[/]")

            elif cmd == "kill":
                if not args:
                    console.print("[red][!] Cú pháp: kill <package_name>[/]")
                else:
                    pkg = args[0]
                    run_adb(["shell", "am", "force-stop", pkg])
                    console.print(f"[bold red][✓] Remote process {pkg} terminated.[/]")

            elif cmd == "untether":
                console.print("[bold yellow][*] PREPARING WIRELESS UNTETHERED LINK...[/]")
                run_adb(["tcpip", "5555"])
                tele = get_device_telemetry()
                time.sleep(1)
                res = run_adb(["connect", f"{tele['ip']}:5555"])
                console.print(f"[bold bright_green][✓] WIRELESS LINK ENGAGED: {res}[/]")
                console.print("[bold bright_cyan][+] Anh có thể rút dây cáp USB ra ngay bây giờ! Máy tính vẫn điều khiển điện thoại qua Wi-Fi 100%.[/]")

            elif cmd == "shell":
                if not args:
                    console.print("[red][!] Cú pháp: shell <lệnh linux>[/]")
                else:
                    out = run_adb(["shell"] + args)
                    console.print(Panel(out or "[dim italic]No output returned[/]", border_style="cyan", title="SHELL OUTPUT"))

            else:
                console.print(f"[red][!] Lệnh không nhận dạng được: '{cmd}'. Gõ 'clear' để xem danh sách lệnh.[/]")

        except KeyboardInterrupt:
            console.print("\n[yellow][!] Operation cancelled by user. Type 'exit' to quit.[/]")
        except Exception as e:
            console.print(f"[red][!] Exception: {e}[/]")

if __name__ == "__main__":
    main_loop()
