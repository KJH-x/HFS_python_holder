# HFS host
# encoding=utf-8
'''
Filename :HFS host.py
Description :N/A
Datatime :2022/08/05
Author :KJH
Version :v1.1
'''
import os
import sys
from traceback import print_exc
os.system("chcp 65001")
os.chdir(sys.path[0])
try:
    para = sys.argv
    if len(para) >= 1:
        para.pop(0)
        parameter = " ".join(para)
    print(parameter)
    os.system("hfs "+parameter)

except Exception or KeyboardInterrupt:
    print_exc()
    input()
