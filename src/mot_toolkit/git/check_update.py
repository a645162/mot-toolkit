import os
import threading


class CheckUpdateThread(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        print("check_update_thread")


def check_update():
    check_update_thread = CheckUpdateThread()
    check_update_thread.start()
