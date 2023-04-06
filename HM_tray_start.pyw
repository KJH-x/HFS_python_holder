import pystray
import win32gui
import win32con
import win32api
import subprocess
import win32process
import os
import sys
from PIL import Image
import ctypes
import time
import json


def toggle_window_visibility(hWnd: int):
    """
    Toggles the visibility of a window by its pid.
    """
    if win32gui.IsWindowVisible(hWnd):
        # Window is visible, hide it
        win32gui.ShowWindow(hWnd, win32con.HIDE_WINDOW)
        return not win32gui.IsWindowVisible(hWnd)
    else:
        win32gui.ShowWindow(hWnd, win32con.SHOW_OPENWINDOW)
        return win32gui.IsWindowVisible(hWnd)


def get_window_by_pid(process: subprocess.Popen) -> int:
    window = 0
    windows = []

    def enum_windows_callback(hWnd: int, lParam):
        if win32process.GetWindowThreadProcessId(hWnd)[1] == process.pid:
            windows.append(hWnd)
    win32gui.EnumWindows(enum_windows_callback, None)
    if len(windows) > 0:
        # If multiple windows are found with the same PID, just use the first one
        window = windows[0]
        return window
    else:
        return 0
    

def on_tray_click(hWnd: int, tray_instance: pystray.Icon):
    """
    Callback function that is called when the tray icon is clicked.
    """
    if not toggle_window_visibility(hWnd):
        terminate_program(tray_instance)


def create_tray_icon(GUI:int):
    """
    Creates a system tray icon using pystray.
    """
    icon_image = Image.open(".\\App\\Icon\\HM_tray.ico")
    tray_instance = pystray.Icon(
        '双击显示/隐藏程序框，右键功能菜单', icon_image, title="HFS_manager")
    tray_instance.menu = pystray.Menu(
        pystray.MenuItem(
            '显示/隐藏', lambda: on_tray_click(GUI,tray_instance)),
        pystray.MenuItem('退出托盘', lambda: terminate_program(tray_instance))
    )
    # tray_instance.title("自动重登")
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
    tray_instance.run()


def terminate_program(tray_instance: pystray.Icon):
    global HFS, FW, GUI, CSW
    GUI.kill()
    tray_instance.stop()


if __name__ == '__main__':
    os.chdir(sys.path[0])

    GUI=subprocess.Popen(
        "python .\\App\\HFS_management.py",
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    while True:
        try:
            with open(".\\App\\Runtime\\GUI.json", "r") as pid_rec:
                pid_dict = dict(json.load(pid_rec))
            print("HFS:", HFS := pid_dict.get("HFS"))
            print("FW:", FW := pid_dict.get("FW"))
            # print("GUI:", GUI := pid_dict.get("GUI"))
            print("CSW:", CSW := pid_dict.get("CSW"))
            time.sleep(1)
            break
        except Exception as e:
            print(e)
            time.sleep(0.5)
            pass
    toggle_window_visibility(get_window_by_pid(GUI))

    create_tray_icon(get_window_by_pid(GUI))
