# encoding=utf-8
'''
Filename :HFS_managememt.py
Datatime :2022/08/10
Author :KJH
Version :v0.7.0
'''
import pyperclip

import os
import sys
import subprocess
from traceback import print_exc
import win32gui
import win32con

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


def read_config():
    yaml_path = ".\\management_config.yaml"
    try:
        # 打开文件
        with open(yaml_path, "r", encoding="utf-8") as config_file:
            data = yaml.load(config_file, Loader=yaml.FullLoader)
            return data
    except:
        input(print_exc())
        exit()


def start_HFS(parameter: str):
    global start_time, url_list, config
    msg_count = 0
    # start HFS via another batch
    command = "python.exe \".\\HFS_host.py\" "+parameter
    hfs = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    logging.info("host batch started")

    # read console feedback, get working ip
    # NEED UPDATE USING IPCONFIG
    if not skip_scan:
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
                logging.info("Appending:"+reply)
            else:
                continue
            msg_count += 1

    # sort the ips, let ipv4 address be the first
    url_list.sort(
        key=len,
        reverse=config["GUI"]["ip_sort_rule"]["reverse"]
    )
    logging.info(url_list)
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
    return img.resize((width, height), Image.Resampling.LANCZOS)


def checkip(address: str):
    version = IPy.IP(address).version()
    return version == 4 or version == 6 or address == "about:blank"


def side_widget(flag=0, content=""):
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
                generateQR(
                    content=content, pic_name=pic_name,
                    fg_color=qrcpfg, bg_color=qrcpbg
                )
                logging.info("copy content qr generated fg:%s bg:%s" %
                             (qrcpfg, qrcpbg))
            elif flag == 0:
                generateQR(
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
    return


def generateQR(content="", pic_name="", fg_color="black", bg_color="white"):
    # make qr image
    qr = qrcode.QRCode(border=0)
    qr.add_data(content)
    qr.make(True)
    img = qr.make_image(CustomImage, fill_color=fg_color, back_color=bg_color)
    img.save(pic_name)
    logging.info("temp image created and saved")
    return


def ADD(name="", row=0, column=0, command=..., colspan=1, fg="white", bg="#3c78aa"):
    global mh
    return tk.Button(text=name, command=command,
                     master=mh, font=font_style_1, fg=fg, bg=bg).grid(row=row, column=column, columnspan=colspan, sticky="WE")


def copy(content=""):
    pyperclip.copy(content)
    logging.info("content \"%s\" copied to clipboard" % content)
    return


def show_console():
    global console_status, console_title
    logging.info("console status before adjust:%s" % console_status)
    if not console_status:
        win32gui.ShowWindow(
            win32gui.FindWindow(0, console_title),
            win32con.SHOW_OPENWINDOW
        )

    else:
        win32gui.ShowWindow(
            win32gui.FindWindow(0, console_title),
            win32con.HIDE_WINDOW
        )

    console_status = not console_status
    logging.info("console status after adjust:%s" % console_status)
    return


def browse(url=""):
    global hfs_port, config
    browser = "" if config["GUI"]["browser"] is None \
        else str(config["GUI"]["browser"])
    url = "http://localhost:"+str(hfs_port) + \
        "/~/admin/"if url == "" else url
    command = "start "+browser+" "+url
    logging.info("browse command:%s" % command)
    subprocess.Popen(command, shell=True,
                     creationflags=subprocess.CREATE_NEW_CONSOLE)
    return


def QUIT():
    global mh, config
    if config["backstage_console"]["close_console_when_quite"]:
        command = "taskkill /im hfs.exe"
        subprocess.Popen(command, shell=True,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        logging.info("HFS.exe killed successfully")
    mh.destroy()
    logging.info("tkinter window destroyed")
    return


if __name__ == "__main__":
    try:
        # Variable preset
        image = photo = None
        console_status = False
        start_time = ""
        pic_name = ".\\temp.png"
        url_list = []
        last_content = ""

        os.system("chcp 65001")
        os.chdir(sys.path[0])

        config = read_config()

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

        if config["GUI"]["skip_ip_scan"]:
            for ip in config["GUI"]["preset_ip"]:
                if checkip(str(ip)):
                    url_list.append("http://"+ip)
            skip_scan = True
        else:
            skip_scan = False
        logging.info("Skip_scan:" + str(skip_scan))

        HFS_parameter = str(config["HFS"]["parameter"])
        hfs_port = config["GUI"]["port"]
        logging.info("Parameter=" + str(HFS_parameter))

        # Console preparation
        if not config["advanced"]["debug_mode"]:

            console_title = str(config["backstage_console"]["title"])
            console_color = str(config["backstage_console"]["console_color"])

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
        start_HFS(HFS_parameter)
        logging.info("start_HFS execute done")

        # Tkinter preparation
        mh = tk.Tk()
        mh.title(config["GUI"]["name"])
        mh.iconbitmap(default=".\\HM.ico")
        mh.configure(bg="#000000")
        mh.protocol("WM_DELETE_WINDOW", QUIT)
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
        logging.info("url, browse, (qr for url) set")

        # control button
        ADD("Open Management", 3, 0, browse, bg=mbbg, fg=mbfg)
        ADD("LOG", 3, 1, show_console, bg=logbg, fg=logfg)
        copy_button = tk.Button(
            mh, text="▶", bg=qrpbg, fg=qrpfg, font=font_style_1,
            command=lambda: side_widget(flag=1)
        )
        copy_button.grid(row=3, column=2, sticky="WNE")
        ADD("❌", 3, 3, QUIT, bg=quitbg, fg=quitfg)
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
