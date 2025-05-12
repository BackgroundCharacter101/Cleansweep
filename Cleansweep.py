import os
import shutil
import tempfile
import psutil
from pathlib import Path
import winshell
import ctypes
import sys

# --- CONFIG ---
USER = os.getlogin()
BASE_PATH = Path(f"C:/Users/{USER}/AppData/Local/SysLogs")
SCREENSHOT_DIR = BASE_PATH / "screenshots"
KEYLOG_FILE = BASE_PATH / "keylog.txt"

SUMMARY = []
FREED_SPACE = 0

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
    except:
        SUMMARY.append("Recycle Bin could not be emptied.")
        return 0


def show_summary():
    print("\n=== CLEANUP SUMMARY ===")
    for line in SUMMARY:
        print(line)
    print(f"Total space freed: {round(FREED_SPACE / (1024*1024), 2)} MB")
    c_drive = psutil.disk_usage('C:/')
    total_gb = round(c_drive.total / (1024**3), 2)
    used_gb = round(c_drive.used / (1024**3), 2)
    free_gb = round(c_drive.free / (1024**3), 2)
    print(f"C:\\ Drive Size: {total_gb} GB total, {used_gb} GB used, {free_gb} GB free")


if __name__ == "__main__":
    FREED_SPACE += clean_temp()
    FREED_SPACE += clean_browser_cache()
    FREED_SPACE += clean_windows_update()
    FREED_SPACE += clean_custom_logs()

    recycle_input = input("Do you want to empty the Recycle Bin? Press Y to yes, N to no: ").strip().upper()
    if recycle_input == 'Y':
        FREED_SPACE += empty_recycle_bin()
    else:
        SUMMARY.append("Recycle Bin skipped by user.")

    show_summary()
    input("\nPress Enter to exit...")
