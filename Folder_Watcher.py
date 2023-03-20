import time
from watchdog.observers import Observer
from watchdog.events import *
import shutil
import re
import json
import os
import sys
from datetime import datetime



class FileCreateHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)

    def on_moved(self, event: FileMovedEvent):
        if re.findall("\$upload", event.src_path) != [] and re.findall("\$upload", event.dest_path) == []:
            file_name = str(event.dest_path).removeprefix(target_folder)
            print(f"[INFO][{report_time()}] MOVE/RENAME:")
            print(f"  - Pattern matched")
            shutil.move(target_folder+file_name, archive_folder+file_name)
            print(f"  - Moved: {file_name}")

        else:
            print(f"[WARN][{report_time()}] Ignored move/rename:")
            print(f"  - is Folder:{event.is_directory}")
            print(f"  - {str(event.src_path).removeprefix(target_folder)}")
            print(f"  - ->")
            print(f"  - {str(event.dest_path).removeprefix(target_folder)}")
            print()

    # def on_any_event(self, event: FileSystemEvent):
    #     print(f"\nANY EVENT:\n{event}\n")


def report_time() -> str:
    return datetime.now().strftime(TLF)


def read_config(filename: str) -> dict:
    """从脚本所在文件夹读取用户信息

    Return:
        - tuple[str, str]: (username, password)
    """
    try:
        config_file = open(filename, "r", encoding="utf8")
        config = json.load(config_file)
        return config

    except FileNotFoundError:
        print(f"[WARN][{report_time()}] 未找到配置文件，正在创建...")
        return write_config(filename)

    except json.decoder.JSONDecodeError:
        print(f"[WARN][{report_time()}] 文件错误，正在重写...")
        return write_config(filename)


def write_config(filename: str) -> tuple[str, str]:
    """写入监控配置文件

    Return:
        - tuple[str, str]: (username, password)
    """
    with open(filename, "w", encoding="utf8") as config_file:
        tf = input(
            f"[INFO][{report_time()}] 请输入监控文件夹路径:").replace("\\", "\\\\")
        af = input(
            f"[INFO][{report_time()}] 请输入转移文件夹路径:").replace("\\", "\\\\")
        config_file.write(
            f"{{\"target_folder\":\"{tf}\",\"archive_folder\":\"{af}\"}}"
        )
    return {"target_folder": tf, "archive_folder": af}


TLF = "%H:%M:%S"

if __name__ == "__main__":
    os.chdir(sys.path[0])
    config = read_config(".\\FW_config.json")
    target_folder = config["target_folder"]
    archive_folder = config["archive_folder"]
    observer = Observer()

    move_handler = FileCreateHandler()

    observer.schedule(move_handler, target_folder, True)
    observer.start()
    print(f"[INFO][{report_time()}] 监控已启动")

    try:
        while True:
            time.sleep(100)

    except KeyboardInterrupt:
        pass

    except Exception as ex:
        print(ex)

    finally:
        observer.stop()
        observer.join()
