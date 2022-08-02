# HFS
# encoding=utf-8
'''
Filename :HFS_managememt.py
Description :N/A
Datatime :2022/08/02
Author :KJH
Version :v6.5
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


def start_HFS(port: int):
    global start_time, http_list
    msg_count = 0

    # start HFS via another batch
    command = "python.exe \".\\HFS_host.py\" --port "+str(port)
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
            http_list.append(reply.replace("- ", ""))
        else:
            continue
        msg_count += 1

    # sort the ips, let ipv4 address be the first
    http_list.sort(key=len)
    print(http_list)
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


def side_widget_control(flag=0, content=""):
    global mh, image, photo, QRslot, last_content
    QRslot.grid_remove
    mh.geometry("")
    content = pyperclip.paste() if content == ""else content
    # printThis()
    ctv = (content == last_content)
    vgs = QRslot.winfo_viewable()
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
                     master=mh, font=FONT_STYLE_1, fg=fg, bg=bg).grid(row=row, column=column, columnspan=colspan, sticky="WE")


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


def open_in_browser(url=""):
    global HFS_port
    url = "http://localhost:"+str(HFS_port)+"/~/admin/"if url == "" else url
    command = "start chrome.exe "+url
    sp.Popen(command, shell=True, creationflags=sp.CREATE_NEW_CONSOLE)
    return


def QUIT():
    global mh
    command="taskkill /im hfs.exe"
    sp.Popen(command, shell=True, creationflags=sp.CREATE_NEW_CONSOLE)
    return mh.destroy()



if __name__ == "__main__":
    # Variable preset
    FONT_STYLE_1 = ("汉真广标", 9)
    FONT_STYLE_2 = ("等线", 8)
    image = photo = None
    console_status = False
    start_time = ""
    http_list = []
    pic_name = ".\\temp.png"
    HFS_port = 8080

    # Console preparation
    os.system("chcp 65001")
    os.chdir(sys.path[0])

    os.system("title HFS")
    os.system("color F0")
    win32gui.SetWindowPos(win32gui.FindWindow(
        0, "HFS"), win32con.HWND_TOPMOST, 300,
        200, 300, 200, win32con.SWP_SHOWWINDOW)

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        # Start main program
        start_HFS(HFS_port)

        # Tkinter preparation
        mh = tk.Tk()
        mh.title("HFS")
        mh.iconbitmap(
            default=u"E:\\STATIC\\Picture\\component\\Tk_Hide.ico")
        mh.configure(bg="#000000")
        mh.protocol("WM_DELETE_WINDOW", QUIT)

        # Widget
        # IPbox and qrcode generator
        buttons = [[
            tk.Button(mh, text=http_list[0], bg="#964246", fg="white",
                      font=FONT_STYLE_2, command=lambda:copy(http_list[0])),
            tk.Button(mh, text=http_list[1], bg="#964246", fg="white",
                      font=FONT_STYLE_2, command=lambda:copy(http_list[1])),
            tk.Button(mh, text=http_list[2], bg="#964246", fg="white",
                      font=FONT_STYLE_2, command=lambda:copy(http_list[2]))
        ], [
            tk.Button(mh, text="🚀", bg="#CCCC00", fg="white",
                      font=FONT_STYLE_1, command=lambda:open_in_browser(url=http_list[0])),
            tk.Button(mh, text="🚀", bg="#CCCC00", fg="white",
                      font=FONT_STYLE_1, command=lambda:open_in_browser(url=http_list[1])),
            tk.Button(mh, text="🚀", bg="#CCCC00", fg="white",
                      font=FONT_STYLE_1, command=lambda:open_in_browser(url=http_list[2]))
        ], [
            tk.Button(mh, text="QR", bg="#27978e", fg="white",
                      font=FONT_STYLE_1, command=lambda:side_widget_control(content=http_list[0])),
            tk.Button(mh, text="QR", bg="#27978e", fg="white",
                      font=FONT_STYLE_1, command=lambda:side_widget_control(content=http_list[1])),
            tk.Button(mh, text="QR", bg="#27978e", fg="white",
                      font=FONT_STYLE_1, command=lambda:side_widget_control(content=http_list[2]))
        ]]
        col_mapping = [0, 2, 3]
        for col in range(0, len(buttons)):
            for row in range(0, len(buttons[col])):
                buttons[col][row].grid(row=row, column=col_mapping[col],
                                       sticky="NWSE", columnspan=2 if col == 0 else 1)

        # control button
        ADD("Open Management", 3, 0, open_in_browser)
        ADD("LOG", 3, 1, show_console, bg="#002036")
        tk.Button(mh, text="▶", bg="#3ed802", fg="white",
                  font=FONT_STYLE_1, command=lambda: side_widget_control(flag=1)).grid(row=3, column=2, sticky="WNE")
        ADD("❌", 3, 3, QUIT, bg="#f03a17")

        # QR slot
        QRslot = tk.Label(mh, height=50)
        QRslot.grid(row=0, column=4, rowspan=4, sticky="WNS")
        QRslot.grid_remove()
        last_content = ""

        # hide console
        win32gui.ShowWindow(win32gui.FindWindow(
            0, "HFS"), win32con.HIDE_WINDOW)

        # display window
        mh.mainloop()

        # end
        win32gui.ShowWindow(win32gui.FindWindow(
            0, "HFS"), win32con.SHOW_OPENWINDOW)
        exit()

    except Exception or KeyboardInterrupt:
        print_exc()
        input()
