# encoding=utf-8
"""
Filename :HFS_managememt.py
Datatime :2022/09/03
Author :KJH
Version :v0.7.8
"""
from time import sleep
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


def read_yaml():
    """
    加载yaml配置文件
    """
    yaml_path = ".\\management_config.yaml"
    try:
        # open config
        with open(yaml_path, "r", encoding="utf-8") as config_file:
            data = yaml.load(config_file, Loader=yaml.FullLoader)
            return data
    except:
        input(print_exc())
        exit()


def get_ip_pool():
    """从控制台获取本机可用ip地址"""
    call_log(1)
    global ipexclude, url_list, hfs_port

    os.system("ipconfig | clip")
    ipconfig = list(set(pyperclip.paste().splitlines()))
    for line in ipconfig:
        # print(line)
        if "Address" in line and "%" not in line:
            potential = line.split(": ", 1)[1]
            v = check_ip(str(potential))
            if v == 4:
                url_list.append(f"http://{potential}:{str(hfs_port)}")
            elif v == 6:
                url_list.append(f"http://[{potential}]:{str(hfs_port)}")
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
    logging.info(url_list)

    call_log(0)
    return


def start_HFS(parameter: str) -> tuple[subprocess.Popen, subprocess.Popen]:
    """
    启动HFS主程序
    """
    call_log(1)
    global start_time, url_list, config, skip_scan

    # start HFS using hfs_host.py
    # command = "python.exe \".\\HFS_host.py\" "+parameter
    # HFS = subprocess.Popen(
    #     command,
    #     shell=True,
    #     stdout=subprocess.PIPE,
    #     stdin=subprocess.PIPE,
    # )
    HFS = subprocess.Popen(
        "hfs "+parameter,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    logging.info("HFS.exe started")

    FW = subprocess.Popen(
        "python .\\Folder_Watcher.py",
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    logging.info("Folder Watcher started")

    if not skip_scan:
        get_ip_pool()

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


def side_widget(flag=0, content=""):
    """
    处理QR小组件的显示
    """
    call_log(1)
    global mh, image, photo, QRslot, last_content

    QRslot.grid_remove
    mh.geometry("")
    logging.info("side widget cleared")

    content = pyperclip.paste() if content == ""else content
    logging.info("qr content:\"%s\"" % str(content))
    if content == "":
        logging.warning("No content. Nothing Done")
        return
    else:

        if content == last_content and QRslot.winfo_viewable():
            QRslot.grid_forget()
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

    image = Image.open(pic_name)
    w_box = h_box = config["GUI"]["size"]["qrsize"]
    image = picture_resize(image, w_box, h_box)
    logging.info("image resized to %d" % config["GUI"]["size"]["qrsize"])

    photo = ImageTk.PhotoImage(image)
    QRslot.configure(image=photo)
    QRslot.grid(row=0, column=4, rowspan=4, sticky="WNS")
    mh.geometry("")
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


def grid_button(name: str, row: int, column: int,
                command: str, fg: str, bg: str,
                colspan=1):
    """
    新建通用按钮，并grid到网格中
    """
    call_log(1)
    global mh

    button_object = tk.Button(
        text=name, command=command, master=mh,
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


def show_console(HFS_process: subprocess.Popen, FW_process: subprocess.Popen, GUI_hwnd: int):
    """
    处理控制台的显示与隐藏（而不是最小化）
    """
    call_log(1)


    HFS_hwnd = get_window_by_pid(HFS_process)
    if win32gui.IsWindowVisible(HFS_hwnd):
        # Window is visible, hide it
        win32gui.ShowWindow(HFS_hwnd, win32con.HIDE_WINDOW)
        logging.info("Hide HFS console")
    else:
        win32gui.ShowWindow(HFS_hwnd, win32con.SHOW_OPENWINDOW)
        logging.info("Show HFS console")

    FW_hwnd = get_window_by_pid(FW_process)
    if win32gui.IsWindowVisible(FW_hwnd):
        # Window is visible, hide it
        win32gui.ShowWindow(FW_hwnd, win32con.HIDE_WINDOW)
        logging.info("Hide FW console")
    else:
        win32gui.ShowWindow(FW_hwnd, win32con.SHOW_OPENWINDOW)
        logging.info("Show FW console")
    
    win32gui.SetForegroundWindow(GUI_hwnd)
    logging.info("GUI brought to top")

    call_log(0)
    return


def browser_open(url=""):
    """
    用浏览器打开指定网址"""
    call_log(1)
    global hfs_port, config

    browser = "" if config["GUI"]["browser"] is None \
        else str(config["GUI"]["browser"])
    url = "http://localhost:"+str(hfs_port) + "/~/admin/"\
        if url == "" else url

    command = "start "+browser+" "+url
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

    def enum_windows_callback(hwnd: int, lParam):
        if win32process.GetWindowThreadProcessId(hwnd)[1] == process.pid:
            windows.append(hwnd)
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
    global mh, config

    if config["backstage_console"]["close_console_when_quite"]:
        HFS_process.kill()
        logging.info("HFS.exe killed successfully")

    FW_process.kill()
    logging.info("Folder Watcher killed successfully")

    mh.destroy()
    logging.info("tkinter window destroyed")

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


if __name__ == "__main__":
    try:
        # Variable preset
        image = photo = None
        start_time = ""
        pic_name = ".\\temp.png"
        url_list = []
        last_content = ""

        os.system("chcp 65001")
        os.chdir(sys.path[0])

        config = read_yaml()
        ipexclude = config["GUI"]["exclude_ip_list"]

        logConfig.dictConfig(config["log"])
        logging.info("Enviroment Preperation Done")

    except Exception:
        print_exc()
        input("Fatal Error...Quiting")
        input("Issue the problem if necessary")
        exit()

    try:
        logging.info("read config successfully")

        font_style_1 = (config["GUI"]["font"]["command_bar"])
        font_style_2 = (config["GUI"]["font"]["url_bar"])

        logging.info("Font set:"+str(font_style_1)+str(font_style_2))

        hfs_port = config["GUI"]["port"]
        if config["GUI"]["skip_ip_scan"]:
            for ip in config["GUI"]["preset_ip_list"]:
                v = check_ip(str(ip))
                if v == 4:
                    url_list.append(f"http://{ip}:{str(hfs_port)}")
                elif v == 6:
                    url_list.append(f"http://[{ip}]:{str(hfs_port)}")
            if len(url_list) < 3:
                for i in range(3-len(url_list)):
                    url_list.append("about:blank")
            skip_scan = True
        else:
            skip_scan = False
        logging.info("Skip_scan:" + str(skip_scan))

        HFS_parameter = str(config["HFS"]["parameter"])
        logging.info("Parameter=" + str(HFS_parameter))

        # Console preparation
        console_title = str(config["backstage_console"]["title"])
        console_color = str(config["backstage_console"]["console_color"])
        if not config["advanced"]["debug_mode"]:

            os.system("title " + console_title)
            logging.info("Console name set:" + console_title)
            os.system("color " + console_color)
            logging.info("Console color set:" + console_color)

            win32gui.SetWindowPos(
                win32gui.FindWindow(0, console_title),
                win32con.HWND_TOPMOST,
                int(config["backstage_console"]["console_loc"]["x"]),
                int(config["backstage_console"]["console_loc"]["y"]),
                int(config["backstage_console"]["console_loc"]["w"]),
                int(config["backstage_console"]["console_loc"]["h"]),
                win32con.SWP_SHOWWINDOW
            )
            logging.info("console_top_most set:" +
                         str(config["backstage_console"]["console_loc"]["x"]) +
                         str(config["backstage_console"]["console_loc"]["y"]) +
                         str(config["backstage_console"]["console_loc"]["w"]) +
                         str(config["backstage_console"]["console_loc"]["h"])
                         )

        # correct_display_dpi
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        logging.info("dpi awareness set")

        # Start main program
        (HFS, FW) = start_HFS(HFS_parameter)
        logging.info("start_HFS execute done")

        # Tkinter preparation
        mh = tk.Tk()
        GUI = mh.winfo_id()
        mh.title(config["GUI"]["name"])
        mh.iconbitmap(default=".\\HM.ico")
        mh.configure(bg="#000000")
        mh.protocol("WM_DELETE_WINDOW", lambda: teminate_main(HFS, FW))
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

        qrcurlbg = str(config["GUI"]["color"]["QR_url_bg"])
        qrcurlfg = str(config["GUI"]["color"]["QR_url_fg"])
        qrcpbg = str(config["GUI"]["color"]["QR_paste_bg"])
        qrcpfg = str(config["GUI"]["color"]["QR_paste_fg"])

        buttons = [[
            tk.Button(mh, text=url_list[0], bg=urlbg, fg=urlfg,
                      font=font_style_2, command=lambda:copy_to_clipboard(url_list[0])),
            tk.Button(mh, text=url_list[1], bg=urlbg, fg=urlfg,
                      font=font_style_2, command=lambda:copy_to_clipboard(url_list[1])),
            tk.Button(mh, text=url_list[2], bg=urlbg, fg=urlfg,
                      font=font_style_2, command=lambda:copy_to_clipboard(url_list[2]))
        ], [
            tk.Button(mh, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browser_open(url=url_list[0])),
            tk.Button(mh, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browser_open(url=url_list[1])),
            tk.Button(mh, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browser_open(url=url_list[2]))
        ], [
            tk.Button(mh, text="QR", bg=sqrbg, fg=sqrfg,
                      font=font_style_1, command=lambda:side_widget(content=url_list[0])),
            tk.Button(mh, text="QR", bg=sqrbg, fg=sqrfg,
                      font=font_style_1, command=lambda:side_widget(content=url_list[1])),
            tk.Button(mh, text="QR", bg=sqrbg, fg=sqrfg,
                      font=font_style_1, command=lambda:side_widget(content=url_list[2]))
        ]]
        col_mapping = [0, 2, 3]
        for col in range(0, len(buttons)):
            for row in range(0, len(buttons[col])):
                buttons[col][row].grid(row=row, column=col_mapping[col],
                                       sticky="NWSE", columnspan=2 if col == 0 else 1)
        logging.info("url, browse, (qr for url) set")

        # control button
        grid_button("Open Management", 3, 0, browser_open, bg=mbbg, fg=mbfg)
        grid_button("LOG", 3, 1, lambda: show_console(
            HFS, FW, GUI), bg=logbg, fg=logfg)
        copy_button = tk.Button(
            mh, text="▶", bg=qrpbg, fg=qrpfg, font=font_style_1,
            command=lambda: side_widget(flag=1)
        )
        copy_button.grid(row=3, column=2, sticky="WNE")
        grid_button("❌", 3, 3, lambda: teminate_main(
            HFS, FW), bg=quitbg, fg=quitfg)
        logging.info("control button set")

        # QR slot
        QRslot = tk.Label(mh, height=config["GUI"]["size"]["qrsize"])

    except Exception:
        logging.exception(print_exc())
        logging.error("tk preperation Error...Quiting")
        input("Check logging file to acquire more detail")
        input("Issue the problem if necessary")
        exit()

    try:
        # hide console
        if config["backstage_console"]["hide_console_immediately"] \
                or not config["advanced"]["debug_mode"]:
            win32gui.ShowWindow(
                win32gui.FindWindow(0, console_title),
                win32con.HIDE_WINDOW
            )
        logging.info("console hidden")

        # display window
        logging.info("showing GUI")
        mh.mainloop()
        logging.info("GUI now destroyed")

        # end
        if config["backstage_console"]["close_console_when_quite"]\
                or not config["advanced"]["debug_mode"]:
            win32gui.ShowWindow(
                win32gui.FindWindow(0, console_title),
                win32con.SHOW_OPENWINDOW
            )
        logging.info("console shown")

    except Exception:
        logging.exception(print_exc())
        logging.error("Main Error...Quiting")
        input("check logging file to acquire more detail")
        input("Issue the problem if necessary")
        exit()
