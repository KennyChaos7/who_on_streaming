import os
import threading
import time
from tkinter import Tk, ttk, Menu, StringVar, Label, messagebox
from typing import Optional
import schedule
import wbi


isKeepLive = True
iniPath = os.getcwd() + '/wos.ini'
columns = ('1', '2', '3', '4')
errorCode = 0
errorMsg = ''
window = Tk()
treeView = ttk.Treeview(window, columns=columns, show='headings')
autoTaskCount = 0
labelText = StringVar()


class GetDataThread(threading.Thread):
    def __init__(self, id, name):
        threading.Thread.__init__(self)
        self.id = id
        self.name = name

    def run(self):
        global autoTaskCount
        autoTaskCount = 0
        get_data()
        schedule.every(3).minutes.do(get_data)
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
        """ % (self.name, self.mid, self.is_on_streaming, self.room_id)

    def __repr__(self):
        return self.name

    @staticmethod
    def keys():
        return ('name', 'mid', 'is_on_streaming', 'room_id')

    def __getitem__(self, item):
        return getattr(self, item)


thread = GetDataThread(name="get_data", id=1)


def search_one_by_mid(mid: str) -> Optional[Liver]:
    response = wbi.get_acc_info(mid=mid)
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


def search_multi_by_mid(mids_list: list) -> Optional[list]:
    response = wbi.get_status_info_by_uids(mids_list)
    print(response.json())
    if response.json()['code'] == 0:
        up_info_list = []
        rsp_json = response.json()
        data_json = rsp_json['data']
        for mid in mids_list:
            if mid in data_json:
                room_json = data_json[mid]
                is_on_streaming = False
                if room_json['live_status'] == 1:
                    is_on_streaming = True
                up_info = Liver(room_json['uname'], str(room_json['uid']), is_on_streaming, str(room_json['room_id']))
                print(up_info)
                up_info_list.append(up_info)
        return up_info_list
    else:
        global errorCode, errorMsg
        errorCode = "错误码" + str(response.json()['code'])
        errorMsg = "接口" + response.json()['message']
        return None


def get_all_mids_from_file():
    mids_str = r""
    mids_list = []
    if not os.path.exists(iniPath):
        # 提示把要查的mid放进wos.ini里，用换行来区分
        open(iniPath, mode='x')
    with open(iniPath) as f:
        str_line = f.readline().replace("\n", '')
        while len(str_line) > 0:
            mids_list.append(str_line)
            mids_str += (str_line + ',')
            str_line = f.readline().replace("\n", '')
    return mids_str[:-1], mids_list


def get_data():
    empty_tree_view()
    global autoTaskCount
    autoTaskCount = autoTaskCount + 1
    update_label_text()
    up_info_list = []

    # 用单个查询接口
    # mids_str, _ = get_all_mids_from_file()
    # for mid in mids:
    #     up_info = search_one_by_mid(mid)
    #     up_info_list.append(up_info)
    # update_tree_view(up_info_list)
    # 用多个同时查询接口
    _, mids_list = get_all_mids_from_file()
    up_info_list = search_multi_by_mid(mids_list)
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
    global isKeepLive, autoTaskCount
    isKeepLive = False
    autoTaskCount = 0
    thread.join()
    window.title("看看谁在直播")


def create_window():
    window.title("看看谁在直播")
    window.geometry('350x260')
    create_menu()
    create_tree_view()
    label = Label(window, textvariable=labelText)
    # label.config(font=("Courier", 14))
    label.grid()
    window.mainloop()


def create_menu():
    menubar = Menu(window)
    menu_config = Menu(menubar, tearoff=0)
    menu_config.add_command(label='开启', command=start_schedule_task)
    menu_config.add_command(label='停止', command=stop_schedule_task)
    menu_config.add_separator()
    menubar.add_cascade(label='选项', menu=menu_config)
    menubar.add_cascade(label='刷新', command=get_data)
    menubar.add_cascade(label='test', command=test)
    window.config(menu=menubar)


def create_tree_view():
    treeView.column('1', width=50, anchor='center')
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
            item = [index, up_info['name'], up_info['mid'], is_on_streaming, up_info['room_id']]
            index = index + 1
            treeView.insert('', 'end', values=item)
            treeView.grid()
    else:
        treeView.insert('', 'end', values=['---', errorMsg, errorCode, ' ---- '])
        treeView.grid()


def get_sort_key(item):
    return item


def update_label_text():
    labelText.set("已经自动执行了" + str(autoTaskCount) + "次监控刷新")


def empty_tree_view():
    item_list = treeView.get_children()
    for item in item_list:
        treeView.delete(item)


def test():
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', ' !!!!!! '])
    treeView.grid()


if __name__ == '__main__':
    create_window()
    # get_all_mids_str_from_file()
    # search_one_by_mid('117906')
    # str_l = list()
    # str_l.append("117906")
    # search_multi_by_mid(str_l)