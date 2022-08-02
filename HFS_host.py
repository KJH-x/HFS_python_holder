# HFS host
# encoding=utf-8
'''
Filename :HFS host.py
Description :N/A
Datatime :2022/05/21
Author :KJH
Version :v1.0
'''
import os
import sys
from traceback import print_exc
os.system("chcp 65001")
os.chdir(sys.path[0])
try:
    para = sys.argv
    # print(para)
    if len(para) > 1 and para[1] == "--port" and para[2].isdigit():
        hfs_port = str(para[2])
        # print(hfs_port)
        os.system("hfs --port "+hfs_port)
except Exception or KeyboardInterrupt:
    print_exc()
    input()
