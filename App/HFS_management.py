# encoding=utf-8
"""
Filename :HFS_managememt.py
Datatime :2022/09/03
Author :KJH
Version :v0.7.8
"""
import pyperclip

import os
import sys
import subprocess
from traceback import print_exc
import win32gui
import win32con
import win32process
import inspect

import ctypes
import tkinter as tk
import qrcode
from PIL import Image, ImageTk, ImageDraw
from qrcode.image.pil import PilImage

import yaml
import json
import IPy
import logging
import logging.config as logConfig


class CustomImage(PilImage):
    """
    自定义图像生成器
    """
    fillcolor = "black"
    backcolor = "white"

    def new_image(self, **kwargs):
        self.fillcolor = kwargs.get('fill_color', 'black')
        self.backcolor = kwargs.get('back_color', 'white')
        img = Image.new(
            "RGB", (self.pixel_size, self.pixel_size), self.backcolor)
        self._idr = ImageDraw.Draw(img)
        return img

    def drawrect(self, row, col):
        box = self.pixel_box(row, col)
        self._idr.rectangle(box, fill=self.fillcolor)


def read_yaml() -> dict:
    """
    加载yaml配置文件
    """
    yaml_path = f"{sys.path[0]}\\Config\\management_config.yaml"
    try:
        # open config
        with open(yaml_path, "r", encoding="utf-8") as config_file:
            data = yaml.load(config_file, Loader=yaml.FullLoader)
            return dict(data)
    except:
        input(print_exc())
        exit()


def get_ip_pool(http_port: int) -> list:
    """从控制台获取本机可用ip地址"""
    call_log(1)
    global ipexclude, url_list

    for line in subprocess.run(
            'ipconfig', capture_output=True, text=True).stdout.splitlines():
        if "Address" in line and "%" not in line:
            potential = line.split(": ", 1)[1].strip()
            v = check_ip(str(potential))
            if v == 4:
                url_list.append(f"http://{potential}:{str(http_port)}")
            elif v == 6:
                url_list.append(f"http://[{potential}]:{str(http_port)}")
            else:
                pass
    if len(url_list) < 3:
        for i in range(3-len(url_list)):
            url_list.append("about:blank")
    for item in ipexclude:
        try:
            url_list.remove(ipexclude[item]) \
                if ipexclude[item] != "about:blank" else 1
        except ValueError:
            logging.warning(str(ipexclude[item])+" is not in list")
            continue
    url_list.sort(
        key=len,
        reverse=config["GUI"]["ip_sort_rule"]["reverse"]
    )
    print(f"Availble url list:\n")
    for url in url_list:
        print(f" - {url}")
    logging.info(url_list)

    call_log(0)
    return url_list


def start_dependency(parameter: str, http_port: int) -> tuple[subprocess.Popen, subprocess.Popen]:
    """
    启动HFS主程序和文件夹监听
    """
    call_log(1)
    global start_time, url_list, skip_scan

    HFS = subprocess.Popen(
        "hfs "+parameter,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    logging.info("HFS.exe started")

    FW = subprocess.Popen(
        f"python {sys.path[0]}\\Folder_Watcher.py",
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    logging.info("Folder Watcher started")

    if not skip_scan:
        get_ip_pool(http_port)

    call_log(0)
    return (HFS, FW)


def picture_resize(img: Image, width: int, height: int):
    """ 
    按给定矩形框的最小比例，对一个img对象进行等比缩放
    """
    call_log(1)
    w, h = img.size
    f1 = width/w
    f2 = height/h
    factor = min([f1, f2])
    width = int(w * factor)
    height = int(h * factor)
    call_log(0)
    return img.resize((width, height), Image.Resampling.LANCZOS)


def check_ip(address: str):
    """确认是否为正确的IP地址，返回真或假"""
    call_log(1)
    try:
        call_log(0)
        return IPy.IP(address).version()
    except ValueError:
        return address == "about:blank"


def toggle_QRcode(parent: tk.Tk, target: tk.Label, flag=0, content=""):
    """
    处理QR小组件的显示
    """
    call_log(1)
    global image, photo, last_content, qr_style

    qrcurlbg, qrcurlfg, qrcpbg, qrcpfg, qr_box_size = qr_style
    target.grid_remove
    parent.geometry("")
    logging.info("side widget cleared")

    content = pyperclip.paste() if content == ""else content
    logging.info("qr content:\"%s\"" % str(content))
    if content == "":
        logging.warning("No content. Nothing Done")
        return
    else:

        if content == last_content and target.winfo_viewable():
            target.grid_forget()
            logging.info("Same content detected, Hiding side widget")
            return
        else:
            if flag == 1:
                generate_QRcode(
                    content=content, pic_name=pic_name,
                    fg_color=qrcpfg, bg_color=qrcpbg
                )
                logging.info("copy content qr generated fg:%s bg:%s" %
                             (qrcpfg, qrcpbg))
            elif flag == 0:
                generate_QRcode(
                    content=content, pic_name=pic_name,
                    fg_color=qrcurlfg, bg_color=qrcurlbg
                )
                logging.info("url content qr generated fg:%s bg:%s" %
                             (qrcpfg, qrcpbg))
            else:
                logging.error("qr parameter error with flag:%d content:%s" %
                              (flag, content))

    image = picture_resize(Image.open(pic_name), qr_box_size, qr_box_size)
    logging.info(f"image resized to {qr_box_size}")

    photo = ImageTk.PhotoImage(image)
    target.configure(image=photo)
    target.grid(row=0, column=4, rowspan=4, sticky="WNS")
    parent.geometry("")
    logging.info("GUI adjusted")

    last_content = content
    logging.info("content recorded (updated):\"%s\"" % last_content)
    os.chdir(sys.path[0])
    os.system("del .\\temp.png")
    logging.info("temp image deleted")
    call_log(0)
    return


def generate_QRcode(content="", pic_name="", fg_color="black", bg_color="white"):
    """
    生成二维码
    """
    call_log(1)
    # make qr image
    qr = qrcode.QRCode(border=0)
    qr.add_data(content)
    qr.make(True)
    img = qr.make_image(
        CustomImage,
        fill_color=fg_color, back_color=bg_color
    )
    img.save(pic_name)
    logging.info("temp image created and saved")
    call_log(0)
    return


def grid_button(tk_window: tk.Tk, name: str, row: int, column: int,
                command, fg: str, bg: str,
                colspan=1):
    """
    新建通用按钮，并grid到网格中
    """
    call_log(1)

    button_object = tk.Button(
        master=tk_window,
        text=name, command=command,
        font=font_style_1, fg=fg, bg=bg
    )
    button_object.grid(
        row=row, column=column,
        columnspan=colspan, sticky="WNE"
    )
    call_log(0)
    return button_object


def copy_to_clipboard(content=""):
    """
    复制到剪贴板
    """
    call_log(1)
    pyperclip.copy(content)
    logging.info("content \"%s\" copied to clipboard" % content)
    call_log(0)
    return


def toggle_visibility(HFS_process: subprocess.Popen, FW_process: subprocess.Popen, GUI_hwnd: int, CSW: int):
    """
    处理控制台的显示与隐藏（而不是最小化）
    """
    call_log(1)

    HFS_hwnd = get_window_by_pid(HFS_process)
    FW_hwnd = get_window_by_pid(FW_process)
    CSW_hwnd = CSW

    if win32gui.IsWindowVisible(HFS_hwnd) or win32gui.IsWindowVisible(FW_hwnd) or win32gui.IsWindowVisible(CSW_hwnd):
        # Window is visible, hide it
        win32gui.ShowWindow(HFS_hwnd, win32con.HIDE_WINDOW)
        logging.info("Hide HFS console")
        win32gui.ShowWindow(FW_hwnd, win32con.HIDE_WINDOW)
        logging.info("Hide FW console")
        win32gui.ShowWindow(CSW_hwnd, win32con.HIDE_WINDOW)
        logging.info("Hide self console")

    else:
        win32gui.ShowWindow(HFS_hwnd, win32con.SHOW_OPENWINDOW)
        logging.info("Show HFS console")
        win32gui.ShowWindow(FW_hwnd, win32con.SHOW_OPENWINDOW)
        logging.info("Show FW console")
        win32gui.ShowWindow(CSW_hwnd, win32con.SHOW_OPENWINDOW)
        logging.info("Show self console")

    try:
        win32gui.SetForegroundWindow(GUI_hwnd)
    except:
        pass
    logging.info("GUI brought to top")

    call_log(0)
    return


def browser_open(url="",):
    """
    用浏览器打开指定网址"""
    call_log(1)
    global browser

    command = f"start {browser} {url} > nul"
    logging.info(f"browse command:{command}")
    subprocess.Popen(
        command,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    call_log(0)
    return


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


def teminate_main(HFS_process: subprocess.Popen, FW_process: subprocess.Popen):
    """
    退出按钮，同时绑定于窗体的关闭键
    """
    call_log(1)
    global tk_window, config, console_policy_2

    if console_policy_2:
        HFS_process.kill()
        logging.info("HFS.exe killed successfully")

    FW_process.kill()
    logging.info("Folder Watcher killed successfully")

    tk_window.destroy()
    logging.info("tkinter window destroyed")
    os.system("del .\\GUI.json")

    call_log(0)
    return


def call_log(status: bool):
    try:
        namelist = inspect.getouterframes(inspect.currentframe())
        name = namelist[1].function
        logging.debug(5*"-" + ("I: " if status else "O: ") + name + 5*"-")
        return True
    except Exception as e:
        logging.error(e)
        return False


def tk_setup(
    config: dict
) -> tuple[tk.Tk, subprocess.Popen, subprocess.Popen, int, tk.Label]:
    global font_style_1, font_style_2, skip_scan

    try:
        logging.info("Font set:"+str(font_style_1)+str(font_style_2))
        http_port = config["GUI"]["port"]

        if skip_scan:
            for ip in config["GUI"]["preset_ip_list"]:
                v = check_ip(str(ip))
                if v == 4:
                    url_list.append(f"http://{ip}:{str(http_port)}")
                elif v == 6:
                    url_list.append(f"http://[{ip}]:{str(http_port)}")
            if len(url_list) < 3:
                for i in range(3-len(url_list)):
                    url_list.append("about:blank")
        logging.info(f"Skip_scan:{str(skip_scan)}")

        HFS_parameter = str(config["HFS"]["parameter"])
        logging.info(f"Parameter={str(HFS_parameter)}")

        # Console preparation
        console_title = str(config["backstage_console"]["title"])

        if not config["advanced"]["debug_mode"]:
            os.system(f"title {console_title}")
            logging.info(f"Console name set:{console_title}")

        # correct_display_dpi
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        logging.info("dpi awareness set")

        # Start main program
        (HFS, FW) = start_dependency(HFS_parameter, http_port)
        logging.info("start_HFS execute done")

        # Tkinter preparation
        tk_window = tk.Tk()
        GUI = tk_window.winfo_id()
        tk_window.title(config["GUI"]["name"])
        tk_window.iconbitmap(default=f"{sys.path[0]}\\Icon\\HM.ico")
        tk_window.configure(bg="#000000")
        tk_window.protocol("WM_DELETE_WINDOW", lambda: teminate_main(HFS, FW))
        logging.info("tkinter window basic config set")

        # tkinter Widget
        # IPbox and qrcode generator
        urlbg = str(config["GUI"]["color"]["copy_url_button_bg"])
        urlfg = str(config["GUI"]["color"]["copy_url_button_fg"])
        brbg = str(config["GUI"]["color"]["browser_button_bg"])
        brfg = str(config["GUI"]["color"]["browser_button_fg"])
        sqrbg = str(config["GUI"]["color"]["QR_url_button_bg"])
        sqrfg = str(config["GUI"]["color"]["QR_url_button_fg"])
        mbbg = str(config["GUI"]["color"]["mamagement_button_bg"])
        mbfg = str(config["GUI"]["color"]["mamagement_button_fg"])
        logbg = str(config["GUI"]["color"]["log_button_bg"])
        logfg = str(config["GUI"]["color"]["log_button_fg"])
        qrpbg = str(config["GUI"]["color"]["QR_paste_button_bg"])
        qrpfg = str(config["GUI"]["color"]["QR_paste_button_fg"])
        quitbg = str(config["GUI"]["color"]["Quit_button_bg"])
        quitfg = str(config["GUI"]["color"]["Quit_button_fg"])

        buttons = [[
            tk.Button(tk_window, text=url_list[0], bg=urlbg, fg=urlfg,
                      font=font_style_2, command=lambda:copy_to_clipboard(url_list[0])),
            tk.Button(tk_window, text=url_list[1], bg=urlbg, fg=urlfg,
                      font=font_style_2, command=lambda:copy_to_clipboard(url_list[1])),
            tk.Button(tk_window, text=url_list[2], bg=urlbg, fg=urlfg,
                      font=font_style_2, command=lambda:copy_to_clipboard(url_list[2]))
        ], [
            tk.Button(tk_window, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browser_open(url=url_list[0])),
            tk.Button(tk_window, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browser_open(url=url_list[1])),
            tk.Button(tk_window, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browser_open(url=url_list[2]))
        ], [
            tk.Button(tk_window, text="QR", bg=sqrbg, fg=sqrfg,
                      font=font_style_1, command=lambda:toggle_QRcode(tk_window, QRslot, content=url_list[0])),
            tk.Button(tk_window, text="QR", bg=sqrbg, fg=sqrfg,
                      font=font_style_1, command=lambda:toggle_QRcode(tk_window, QRslot, content=url_list[1])),
            tk.Button(tk_window, text="QR", bg=sqrbg, fg=sqrfg,
                      font=font_style_1, command=lambda:toggle_QRcode(tk_window, QRslot, content=url_list[2]))
        ]]
        col_mapping = [0, 2, 3]
        for col in range(0, len(buttons)):
            for row in range(0, len(buttons[col])):
                buttons[col][row].grid(row=row, column=col_mapping[col],
                                       sticky="NWSE", columnspan=2 if col == 0 else 1)
        logging.info("url, browse, (qr for url) set")

        # control button
        grid_button(tk_window, "Open Management", 3, 0,
                    lambda: browser_open(url=f"http://localhost:{http_port}/~/admin/"), bg=mbbg, fg=mbfg)
        grid_button(tk_window, "Consoles", 3, 1,
                    lambda: toggle_visibility(HFS, FW, GUI, CSW),
                    bg=logbg, fg=logfg)
        copy_button = tk.Button(
            tk_window, text="▶", bg=qrpbg, fg=qrpfg, font=font_style_1,
            command=lambda: toggle_QRcode(tk_window, QRslot, flag=1)
        )
        copy_button.grid(row=3, column=2, sticky="WNE")
        grid_button(tk_window, "❌", 3, 3,
                    lambda: teminate_main(HFS, FW),
                    bg=quitbg, fg=quitfg)
        logging.info("control button set")

        # QR slot
        QRslot = tk.Label(tk_window, height=config["GUI"]["size"]["qrsize"])

        return (tk_window, HFS, FW, GUI, QRslot)

    except Exception:
        logging.exception(print_exc())
        logging.error("tk preperation Error...Quiting")
        input("Check logging file to acquire more detail")
        input("Issue the problem if necessary")
        exit()


def get_console_window_handle() -> int:
    kernel32 = ctypes.windll.kernel32
    kernel32.GetConsoleWindow.restype = ctypes.c_void_p
    hWnd = kernel32.GetConsoleWindow()
    return hWnd


def write_window_pid(HFS: subprocess.Popen, FW: subprocess.Popen, GUI: int, CSW:int):
    HFS_hwnd = get_window_by_pid(HFS)
    FW_hwnd = get_window_by_pid(FW)
    CSW_hwnd = CSW
    with open(".\\GUI.json", "w") as pid_rec:
        pids = {"HFS": HFS_hwnd, "FW": FW_hwnd, "GUI": GUI, "CSW": CSW_hwnd}
        json.dump(pids, pid_rec, indent=4)

if __name__ == "__main__":
    try:
        # Variable preset
        image = photo = None
        start_time = ""
        pic_name = ".\\temp.png"
        url_list = []
        last_content = ""
        # Get handle of the window
        CSW = get_console_window_handle()

        os.system("chcp 65001 > nul")
        if not os.path.exists(sys.path[0]+"\\Runtime"):
            os.mkdir(sys.path[0]+"\\Runtime")
        os.chdir(sys.path[0]+"\\Runtime")
        print(f"Working Directory: {sys.path[0]}\\Runtime")

        config = read_yaml()
        ipexclude = config["GUI"]["exclude_ip_list"]

        logConfig.dictConfig(config["log"])
        logging.info("Enviroment Preperation Done")

    except Exception:
        print_exc()
        input("Fatal Error...Quiting")
        input("Issue the problem if necessary")
        exit()

    font_style_1 = (config["GUI"]["font"]["command_bar"])
    font_style_2 = (config["GUI"]["font"]["url_bar"])
    skip_scan = config["GUI"]["skip_ip_scan"]
    console_policy_1 = config["backstage_console"]["hide_console_immediately"] or not config["advanced"]["debug_mode"]
    console_policy_2 = config["backstage_console"]["close_console_when_quite"] or not config["advanced"]["debug_mode"]

    qr_style = [config["GUI"]["color"]["QR_url_bg"],
                config["GUI"]["color"]["QR_url_fg"],
                config["GUI"]["color"]["QR_paste_bg"],
                config["GUI"]["color"]["QR_paste_fg"],
                config["GUI"]["size"]["qrsize"],
                ]
    browser = "" if config["GUI"]["browser"] is None \
        else str(config["GUI"]["browser"])

    tk_window, HFS, FW, GUI, QRslot = tk_setup(config)
    del config

    try:
        # hide console
        if console_policy_1:
            toggle_visibility(HFS, FW, GUI, CSW)

        write_window_pid(HFS, FW, GUI, CSW)
        # display window
        logging.info("showing GUI")
        tk_window.mainloop()
        logging.info("GUI now destroyed")

        # end
        if console_policy_2:
            win32gui.ShowWindow(CSW, win32con.SHOW_OPENWINDOW)
        logging.info("console shown")

    except Exception:
        logging.exception(print_exc())
        logging.error("Main Error...Quiting")
        input("check logging file to acquire more detail")
        input("Issue the problem if necessary")
        exit()
