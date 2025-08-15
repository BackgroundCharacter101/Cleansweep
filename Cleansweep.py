import os
import tempfile
import psutil
from pathlib import Path
import winshell
import ctypes
import sys
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel

# --- CONFIG ---
USER = os.getlogin()
BASE_PATH = Path(f"C:/Users/{USER}/AppData/Local/SysLogs")
SCREENSHOT_DIR = BASE_PATH / "screenshots"
KEYLOG_FILE = BASE_PATH / "keylog.txt"

SUMMARY = []
FREED_SPACE = 0
console = Console()

# Check for admin rights
if not ctypes.windll.shell32.IsUserAnAdmin():
    print("Requesting admin privileges...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

def get_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                fp = os.path.join(root, f)
                total += os.path.getsize(fp)
            except:
                pass
    return total

def secure_delete_file(path):
    try:
        if os.path.isfile(path):
            length = os.path.getsize(path)
            # overwrite with random bytes
            with open(path, 'ba+', buffering=0) as f:
                f.seek(0)
                f.write(os.urandom(length))
            os.remove(path)
            return length
    except:
        return 0
    return 0

def secure_delete_folder(path):
    total = 0
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                total += secure_delete_file(os.path.join(root, name))
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except:
                    pass
        try:
            os.rmdir(path)
        except:
            pass
    return total


def clean_temp():
    temp_dirs = [tempfile.gettempdir(), f"C:/Windows/Temp"]
    total = 0
    for temp_dir in temp_dirs:
        total += secure_delete_folder(temp_dir)
    SUMMARY.append(f"System temp files cleaned: {round(total / (1024*1024), 2)} MB")
    return total


def clean_browser_cache():
    chrome_cache = Path(f"C:/Users/{USER}/AppData/Local/Google/Chrome/User Data/Default/Cache")
    edge_cache = Path(f"C:/Users/{USER}/AppData/Local/Microsoft/Edge/User Data/Default/Cache")
    total = 0
    for path in [chrome_cache, edge_cache]:
        total += secure_delete_folder(path)
    SUMMARY.append(f"Browser cache cleaned: {round(total / (1024*1024), 2)} MB")
    return total


def clean_windows_update():
    paths = [
        Path("C:/Windows/SoftwareDistribution/Download"),
        Path("C:/Windows/DeliveryOptimization")
    ]
    total = 0
    for p in paths:
        total += secure_delete_folder(p)
    SUMMARY.append(f"Windows update leftovers cleaned: {round(total / (1024*1024), 2)} MB")
    return total


def clean_custom_logs():
    total = 0
    if SCREENSHOT_DIR.exists():
        total += secure_delete_folder(SCREENSHOT_DIR)
    if KEYLOG_FILE.exists():
        total += secure_delete_file(KEYLOG_FILE)
    SUMMARY.append(f"Custom keylogger/screenlog traces removed: {round(total / (1024*1024), 2)} MB")
    return total


def empty_recycle_bin():
    try:
        before = psutil.disk_usage('C:/').free
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        after = psutil.disk_usage('C:/').free
        freed = after - before
        SUMMARY.append(f"Recycle Bin emptied: {round(freed / (1024*1024), 2)} MB")
        return freed
    except Exception:
        SUMMARY.append("Recycle Bin could not be emptied.")
        return 0


def show_summary():
    console.rule("Cleanup Summary")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Item", style="dim")
    table.add_column("Details")
    for line in SUMMARY:
        table.add_row(line.split(':', 1)[0], line.split(':', 1)[1].strip() if ':' in line else '')
    table.add_row("Total space freed", f"{round(FREED_SPACE / (1024*1024), 2)} MB")
    c_drive = psutil.disk_usage('C:/')
    total_gb = round(c_drive.total / (1024**3), 2)
    used_gb = round(c_drive.used / (1024**3), 2)
    free_gb = round(c_drive.free / (1024**3), 2)
    table.add_row("C:\\ Drive", f"{total_gb} GB total, {used_gb} GB used, {free_gb} GB free")
    console.print(table)


if __name__ == "__main__":
    actions = [
        ("Clean system temp", clean_temp),
        ("Clean browser cache", clean_browser_cache),
        ("Clean Windows update files", clean_windows_update),
        ("Clean custom logs", clean_custom_logs),
    ]

    console.print(Panel("[bold cyan]Welcome to Cleansweep[/]"))

    # run actions with progress
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), TimeElapsedColumn(), console=console) as progress:
        task = progress.add_task("Overall", total=len(actions))
        for desc, func in actions:
            sub_task = progress.add_task(desc, total=1)
            # perform action and simulate progress
            try:
                result = func()
                FREED_SPACE += result
                progress.update(sub_task, advance=1)
            except Exception as e:
                SUMMARY.append(f"{desc}: failed ({e})")
            progress.update(task, advance=1)
            time.sleep(0.2)

    # ask about recycle bin
    if console.input("Do you want to empty the Recycle Bin? ([green]y[/]/[red]n[/]) ").strip().lower().startswith('y'):
        with console.status("Emptying Recycle Bin..."):
            freed = empty_recycle_bin()
            FREED_SPACE += freed
    else:
        SUMMARY.append("Recycle Bin skipped by user.")

    show_summary()
    console.input("\nPress Enter to exit...")
