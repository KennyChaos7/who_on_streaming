import os, requests, time, threading
import tkinter
from tkinter import Tk, ttk, Menu
from typing import Optional

import schedule
import wbi

isKeepLive = True
iniPath = os.getcwd() + '/wos.ini'
os.environ['NO_PROXY'] = 'https://api.bilibili.com'
reqUrl = 'https://api.bilibili.com/x/space/wbi/acc/info'
reqHeaders = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Content-Encoding': 'gzip',
    'Accept': 'application/json',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'close'
}
columns = ('1', '2', '3', '4')
wts = ''
w_rid = ''
errorCode = 0
errorMsg = ''
window = Tk()
treeView = ttk.Treeview(window, columns=columns, show='headings')


class GetDataThread(threading.Thread):
    def __init__(self, id, name):
        threading.Thread.__init__(self)
        self.id = id
        self.name = name

    def run(self):
        search_by_mid_list()
        schedule.every(60).seconds.do(search_by_mid_list)
        while isKeepLive:
            schedule.run_pending()  # 运行所有可以运行的任务
            time.sleep(1)


class Liver:
    def __init__(self, name, mid, is_on_streaming, room_id):
        self.name = name
        self.mid = mid
        self.is_on_streaming = is_on_streaming
        self.room_id = room_id

    def __str__(self):
        return """
        {
            "name":"%s",
            "mid":"%s",
            "is_on_streaming":"%s",
            "room_id":"%s"
        }
        """ %(self.name, self.mid, self.is_on_streaming, self.room_id)

    def __repr__(self):
        return self.name


    @staticmethod
    def keys():
        return ('name', 'mid', 'is_on_streaming', 'room_id')


    def __getitem__(self, item):
        return getattr(self, item)


thread = GetDataThread(name="get_data", id=1)


def search_by_mid(mid: str) -> Optional[Liver]:
    global wts, w_rid
    wts, w_rid = wbi.get_wts_w_rid()
    req_params = {
        "mid": mid,
        'w_rid': w_rid,
        'wts': wts
    }
    response = requests.get(url=reqUrl, params=req_params, headers=reqHeaders)
    print(response.json())
    if response.json()['code'] == 0:
        data_json = response.json()['data']
        room_json = data_json['live_room']
        is_on_streaming = False
        room_id = "-1"
        if room_json is not None and room_json['roomStatus'] == 1:
            room_id = room_json['roomid']
            if room_json['liveStatus'] == 1:
                is_on_streaming = True
        up_info = Liver(data_json['name'], data_json['mid'], is_on_streaming, room_id)
        print(up_info)
        return up_info
    else:
        global errorCode, errorMsg
        errorCode = "错误码" + str(response.json()['code'])
        errorMsg = "接口" + response.json()['message']
        return None


def search_by_mid_list():
    # global wts, w_rid
    # wts, w_rid = wbi.get_wts_w_rid()
    # print("search_by_mid_list")
    up_info_list = []
    empty_tree_view()
    if not os.path.exists(iniPath):
        # 提示把要查的mid放进wos.ini里，用换行来区分
        open(iniPath, mode='x')
    with open(iniPath) as f:
        str_line = f.readline().replace("\n", '')
        while len(str_line) > 0:
            up_info = search_by_mid(str_line)
            if up_info is not None:
                up_info_list.append(dict(up_info))
            str_line = f.readline().replace("\n", '')
    print(up_info_list)
    update_tree_view(up_info_list)


def start_schedule_task():
    print("start_schedule_task")
    global isKeepLive, thread
    isKeepLive = True
    if not thread.is_alive():
        thread = GetDataThread(name="get_data", id=1)
    thread.start()
    window.title("开播监控已经启动")


def stop_schedule_task():
    print("stop_schedule_task")
    global isKeepLive
    isKeepLive = False
    thread.join()
    window.title("看看谁在直播")


def create_window():
    window.title("看看谁在直播")
    window.geometry('400x250')
    create_menu()
    create_tree_view()
    window.mainloop()


def create_menu():
    menubar = Menu(window)
    menu_config = Menu(menubar, tearoff=0)
    menu_config.add_command(label='开启', command=start_schedule_task)
    menu_config.add_command(label='停止', command=stop_schedule_task)
    menu_config.add_separator()
    menubar.add_cascade(label='选项', menu=menu_config)
    menubar.add_cascade(label='刷新', command=search_by_mid_list)
    menubar.add_cascade(label='test', command=test)
    window.config(menu=menubar)


def create_tree_view():
    treeView.column('1', width=100, anchor='center')
    treeView.column('2', width=100, anchor='center')
    treeView.column('3', width=100, anchor='center')
    treeView.column('4', width=100, anchor='center')
    treeView.heading('1', text='序号')
    treeView.heading('2', text='up名称')
    treeView.heading('3', text='uid/mid')
    treeView.heading('4', text='是否直播中')
    # scrollbar = ttk.Scrollbar(window, orient=tkinter.VERTICAL, command=treeView.yview)
    # treeView.configure(yscrollcommand=scrollbar.set)
    # scrollbar.grid(row=0, column=1, sticky='ns')


def update_tree_view(up_info_list):
    if len(up_info_list) > 0:
        index = 0
        for up_info in up_info_list:
            is_on_streaming = '不在直播'
            if up_info['room_id'] == -1:
                is_on_streaming = '该up没有开通直播'
            elif up_info['is_on_streaming']:
                is_on_streaming = '直播中'
            item = [index, up_info['name'], up_info['mid'], is_on_streaming]
            index = index + 1
            treeView.insert('', 'end', values=item)
            treeView.grid()
    else:
        treeView.insert('', 'end', values=['---', errorMsg, errorCode, ' ---- '])
        treeView.grid()


def empty_tree_view():
    item_list = treeView.get_children()
    for item in item_list:
        treeView.delete(item)


def test():
    treeView.insert('', 'end', values=[len(treeView.get_children()),errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- '])
    treeView.grid()


if __name__ == '__main__':
    create_window()
    # search_by_mid('117906')
