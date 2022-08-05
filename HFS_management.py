# using yaml
# encoding=utf-8
'''
Filename :HFS_managememt.py
Description :N/A
Datatime :2022/08/05
Author :KJH
Version :v0.6.7
'''
import os
import subprocess as sp
import sys
from traceback import print_exc
import pyperclip
import win32gui
import win32con
import ctypes
import tkinter as tk
import qrcode
from PIL import Image, ImageTk, ImageDraw
from qrcode.image.pil import PilImage
import yaml
import IPy


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


def read_config():
    yaml_path = ".\\management_config.yaml"
    try:
        # 打开文件
        with open(yaml_path, "r", encoding="utf-8") as config_file:
            data = yaml.load(config_file, Loader=yaml.FullLoader)
            return data
    except:
        print_exc()
        input()
        exit()


def start_HFS(parameter: str):
    global start_time, url_list, config
    msg_count = 0
    # start HFS via another batch
    command = "python.exe \".\\HFS host2.py\" "+parameter
    hfs = sp.Popen(command, shell=True, stdout=sp.PIPE, stdin=sp.PIPE)

    # read console feedback, get right ip
    # NEED UPDATE USING IPCONFIG
    while True:
        reply = hfs.stdout.readline().strip().decode()
        if "started" in reply:
            start_time = reply.replace("started ", "")
        elif "network" in reply[0:10]:
            if "Ethernet" in reply or "WLAN" in reply:
                continue
            else:
                break
        elif "- http" in reply:
            url_list.append(reply.replace("- ", ""))
        else:
            continue
        msg_count += 1

    # sort the ips, let ipv4 address be the first
    url_list.sort(key=len,
                  reverse=config["GUI"]["ip_sort_rule"]["reverse"]
                  )
    print(url_list)
    return


def picture_resize(img: Image, width: int, height: int):
    ''' 
    按给定矩形框的最小比例，对一个img对象进行等比缩放
    '''
    w, h = img.size
    f1 = width/w
    f2 = height/h
    factor = min([f1, f2])
    width = int(w*factor)
    height = int(h*factor)
    return img.resize((width, height), Image.ANTIALIAS)


def checkip(address: str):
    try:
        version = IPy.IP(address).version()
        return version == 4 or version == 6 or version == "about:blank"
    except Exception:
        return print_exc()


def side_widget(flag=0, content=""):
    global mh, image, photo, QRslot, last_content
    QRslot.grid_remove
    mh.geometry("")
    content = pyperclip.paste() if content == ""else content
    if content == last_content and QRslot.winfo_viewable():
        QRslot.grid_forget()
        return
    if flag == 1:
        # get content
        if content == "":
            return
        else:
            generateQR(content=content, pic_name=pic_name,
                       fg_color="#3ed802", bg_color="white")
    elif flag == 0:
        generateQR(content=content, pic_name=pic_name,
                   fg_color="#27978e", bg_color="white")
    else:
        print("qr parameter error", flag, content)

    image = Image.open(pic_name)
    w_box = h_box = 100
    image = picture_resize(image, w_box, h_box)
    photo = ImageTk.PhotoImage(image)
    QRslot.configure(image=photo)
    QRslot.grid(row=0, column=4, rowspan=4, sticky="WNS")
    mh.geometry("")
    last_content = content
    os.chdir(sys.path[0])
    os.system("del .\\temp.png")
    return


def generateQR(content="", pic_name="", fg_color="black", bg_color="white"):
    # make qr image
    qr = qrcode.QRCode(border=0)
    print("qrhttp", content)
    qr.add_data(content)
    qr.make(True)
    img = qr.make_image(CustomImage, fill_color=fg_color, back_color=bg_color)
    img.save(pic_name)
    return


def ADD(name="", row=0, column=0, command=..., colspan=1, fg="white", bg="#3c78aa"):
    global mh
    return tk.Button(text=name, command=command,
                     master=mh, font=font_style_1, fg=fg, bg=bg).grid(row=row, column=column, columnspan=colspan, sticky="WE")


def copy(content=""):
    return pyperclip.copy(content)


def show_console():
    global console_status
    if not console_status:
        win32gui.ShowWindow(win32gui.FindWindow(
            0, "HFS"), win32con.SHOW_OPENWINDOW)
    else:
        win32gui.ShowWindow(win32gui.FindWindow(
            0, "HFS"), win32con.HIDE_WINDOW)
    console_status = not console_status
    return


def browse(url=""):
    global hfs_port, config
    browser = "" if config["GUI"]["browser"] is None \
        else str(config["GUI"]["browser"])
    url = "http://localhost:"+str(hfs_port) + \
        "/~/admin/"if url == "" else url
    command = "start "+browser+" "+url
    sp.Popen(command, shell=True, creationflags=sp.CREATE_NEW_CONSOLE)
    return


def QUIT():
    global mh, config
    if config["backstage_console"]["close_console_when_quite"]:
        command = "taskkill /im hfs.exe"
        sp.Popen(command, shell=True, creationflags=sp.CREATE_NEW_CONSOLE)
    return mh.destroy()


if __name__ == "__main__":
    # Variable preset
    image = photo = None
    console_status = False
    start_time = ""
    pic_name = ".\\temp.png"
    url_list = []
    last_content = ""

    os.system("chcp 65001")
    os.chdir(sys.path[0])

    try:
        config = read_config()
        font_style_1 = (str(config["GUI"]["font"]["command_bar"]), 8)
        font_style_2 = (str(config["GUI"]["font"]["url_bar"]), 8)
        if config["GUI"]["skip_ip_scan"]:
            for ip in config["GUI"]["preset_ip"]:
                if checkip(str(ip)):
                    url_list.append("http://"+ip)
            skip_scan = True
        else:
            skip_scan = False
        HFS_parameter = str(config["HFS"]["parameter"])
        hfs_port = config["GUI"]["port"]

        # Console preparation
        if not config["advanced"]["debug_mode"]:
            os.system("title "+str(config["backstage_console"]["title"]))
            os.system(
                "color "+str(config["backstage_console"]["console_color"]))

            win32gui.SetWindowPos(
                win32gui.FindWindow(0, "HFS"),
                win32con.HWND_TOPMOST,
                int(config["backstage_console"]["console_loc"]["x"]),
                int(config["backstage_console"]["console_loc"]["y"]),
                int(config["backstage_console"]["console_loc"]["w"]),
                int(config["backstage_console"]["console_loc"]["h"]),
                win32con.SWP_SHOWWINDOW
            )

        # correct_display_dpi
        ctypes.windll.shcore.SetProcessDpiAwareness(1)

        # Start main program
        start_HFS(HFS_parameter)

        # Tkinter preparation
        mh = tk.Tk()
        mh.title("HFS")
        mh.iconbitmap(default=".\\HM.ico")
        mh.configure(bg="#000000")
        mh.protocol("WM_DELETE_WINDOW", QUIT)

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
                      font=font_style_2, command=lambda:copy(url_list[0])),
            tk.Button(mh, text=url_list[1], bg=urlbg, fg=urlfg,
                      font=font_style_2, command=lambda:copy(url_list[1])),
            tk.Button(mh, text=url_list[2], bg=urlbg, fg=urlfg,
                      font=font_style_2, command=lambda:copy(url_list[2]))
        ], [
            tk.Button(mh, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browse(url=url_list[0])),
            tk.Button(mh, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browse(url=url_list[1])),
            tk.Button(mh, text="🚀", bg=brbg, fg=brfg,
                      font=font_style_1, command=lambda:browse(url=url_list[2]))
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

        # control button
        ADD("Open Management", 3, 0, browse, bg=mbbg, fg=mbfg)
        ADD("LOG", 3, 1, show_console, bg=logbg, fg=logfg)
        tk.Button(mh, text="▶",
                  bg=qrpbg, fg=qrpfg, font=font_style_1,
                  command=lambda: side_widget(flag=1)
                  ).grid(row=3, column=2, sticky="WNE")
        ADD("❌", 3, 3, QUIT, bg=quitbg, fg=quitfg)

        # QR slot
        QRslot = tk.Label(mh, height=50)
        # QRslot.grid(row=0, column=4, rowspan=4, sticky="WNS")
        # QRslot.grid_remove()

        # hide console
        if config["backstage_console"]["hide_console_immediately"] \
                or not config["advanced"]["debug_mode"]:
            win32gui.ShowWindow(
                win32gui.FindWindow(0, "HFS"),
                win32con.HIDE_WINDOW
            )

        # display window
        mh.mainloop()

        # end
        if config["backstage_console"]["close_console_when_quite"]\
                or not config["advanced"]["debug_mode"]:
            win32gui.ShowWindow(
                win32gui.FindWindow(0, "HFS"),
                win32con.SHOW_OPENWINDOW
            )

    except Exception or KeyboardInterrupt:
        print_exc()
        input()
