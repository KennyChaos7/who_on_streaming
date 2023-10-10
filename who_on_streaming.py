import os, requests, time, threading
from tkinter import *
import schedule
import wbi

window = Tk()
isKeepLive = True
iniPath = os.getcwd() + '/wos.ini'
reqUrl = 'https://api.bilibili.com/x/space/wbi/acc/info'
reqHeaders = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Content-Encoding': 'gzip',
    'Accept': 'application/json',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}


class GetDataThread(threading.Thread):
    def __init__(self, id, name):
        threading.Thread.__init__(self)
        self.id = id
        self.name = name

    def run(self):
        schedule.every(5).seconds.do(search_by_mid_list)
        while isKeepLive:
            schedule.run_pending()  # 运行所有可以运行的任务
            time.sleep(1)

thread = GetDataThread(name="get_data", id=1)



def search_by_mid(mid: str):
    wts, w_rid = wbi.get_wts_w_rid()
    req_params = {
        "mid": mid,
        'w_rid': w_rid,
        'wts': wts
    }
    response = requests.get(url=reqUrl, params=req_params, headers=reqHeaders)
    print(response.json())


def search_by_mid_list():
    print("search_by_mid_list")


def start_schedule_task():
    print("start_schedule_task")
    # if os.path.exists(iniPath):
    #     with open(iniPath) as f:
    #         print(f)
    # else:
    #     ## 提示把要查的mid放进wos.ini里，用换行来区分
    #     open(iniPath, mode='x')
    global isKeepLive
    isKeepLive = False
    thread.start()


def stop_schedule_task():
    print("stop_schedule_task")
    global isKeepLive
    isKeepLive = False
    thread.join()


def override_ini():
    if os.path.exists(iniPath):
        with open(iniPath) as f:
            print(f)


def create_window():
    window.title("看看谁在直播")
    window.geometry('300x500')
    create_menu()

    window.mainloop()


def create_menu():
    menubar = Menu(window)
    menu_config = Menu(menubar, tearoff=0)
    menu_config.add_command(label='开启', command=start_schedule_task)
    menu_config.add_command(label='停止', command=stop_schedule_task)
    menu_config.add_separator()
    menu_config.add_command(label='退出', command=stop_schedule_task)
    menubar.add_cascade(label='选项', menu=menu_config)
    window.config(menu=menubar)


if __name__ == '__main__':
    create_window()
    # search_by_mid('117906')
