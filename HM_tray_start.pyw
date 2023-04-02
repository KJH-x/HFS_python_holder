import pystray
import win32gui
import win32con
import win32process
import subprocess
import os
import sys
from PIL import Image
import ctypes
import time


def toggle_window_visibility(handle: int):
    """
    Toggles the visibility of a window by its handle.
    """

    if win32gui.IsWindowVisible(handle):
        # Window is visible, hide it
        win32gui.ShowWindow(handle, win32con.HIDE_WINDOW)
    else:
        win32gui.ShowWindow(handle, win32con.SHOW_OPENWINDOW)


def get_window_by_pid(process: subprocess.Popen) -> int:
    window = 0
    windows = []

    def enum_windows_callback(hwnd: int, lParam):
        if win32process.GetWindowThreadProcessId(hwnd)[1] == process.pid:
            windows.append(hwnd)
    win32gui.EnumWindows(enum_windows_callback, None)
    if len(windows) > 0:
        # If multiple windows are found with the same PID, just use the first one
        window = windows[0]
        # Return Handle
        return window

    else:
        return 0


def on_tray_click(process: subprocess.Popen, tray_instance: pystray.Icon):
    """
    Callback function that is called when the tray icon is clicked.
    """
    handle = get_window_by_pid(process)
    if handle:
        toggle_window_visibility(handle)
    else:
        terminate_program(process, tray_instance)


def create_tray_icon(process: subprocess.Popen):
    """
    Creates a system tray icon using pystray.
    """
    icon_image = Image.open(".\\HM_tray.ico")
    tray_instance = pystray.Icon(
        '双击显示/隐藏程序框，右键功能菜单', icon_image, title="HFS_manager")
    tray_instance.menu = pystray.Menu(
        pystray.MenuItem(
            '显示/隐藏', lambda: on_tray_click(process, tray_instance)),
        pystray.MenuItem('退出托盘', lambda: terminate_program(
            process, tray_instance))
    )
    # tray_instance.title("自动重登")
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
    tray_instance.run()


def terminate_program(process: subprocess.Popen, tray_instance: pystray.Icon):
    tray_instance.stop()


if __name__ == '__main__':
    os.chdir(sys.path[0])

    Network_Alive = subprocess.Popen(
        "python .\\HFS_management.py",
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    print("wait 5s")
    time.sleep(3)
    toggle_window_visibility(get_window_by_pid(Network_Alive))

    create_tray_icon(Network_Alive)
