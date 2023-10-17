import os
import threading
import time
import winsound
import tkinter
from tkinter import StringVar, IntVar, Tk, ttk, Menu, Label, messagebox, Button
from ttkwidgets import CheckboxTreeview
from typing import Optional, Any
import schedule
import wbi


# 线程类
class GetDataThread(threading.Thread):
    def __init__(self, id, name):
        threading.Thread.__init__(self)
        self.id = id
        self.name = name

    def run(self):
        global autoTaskCount
        autoTaskCount = 0
        get_data()
        # 定时任务3分钟
        schedule.every(3).minutes.do(get_data)
        while isKeepLive:
            schedule.run_pending()  # 运行所有可以运行的任务
            time.sleep(1)


# up主类
class Liver:
    # （up名称，mid/uid，是否已经开播，直播房间号）
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


isKeepLive = True
iniPath = os.getcwd() + '/wos.ini'
columns = ('#1', '#2', '#3', '#4')
checkedList = []
oldUpInfoList = []
errorCode = 0
errorMsg = ''
rootWindow = Tk()
# treeView = ttk.Treeview(window, columns=columns, show='headings')
treeView = CheckboxTreeview(rootWindow, columns=columns, show=('headings', 'tree'))
autoTaskCount = 0
labelText = StringVar()
thread = GetDataThread(name="get_data", id=1)


# 通过单一mid查询用户信息
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


# 通过同时查询多个用户信息
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


# 从ini文件终获得mid列表
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


# 查询数据
def get_data():
    clear_tree_view()
    global autoTaskCount, oldUpInfoList
    autoTaskCount = autoTaskCount + 1
    update_label_text("已经自动执行了" + str(autoTaskCount) + "次监控刷新")
    up_info_list = []

    # 用单个查询接口
    # mids_str, _ = get_all_mids_from_file()
    # for mid in mids:
    #     up_info = search_one_by_mid(mid)
    #     up_info_list.append(up_info)
    # 用多个同时查询接口
    _, mids_list = get_all_mids_from_file()
    up_info_list = search_multi_by_mid(mids_list)

    # 检查是否需要进行提醒
    check_alert_state_and_pop(up_info_list)
    insert_tree_view(up_info_list)
    oldUpInfoList = up_info_list


# 开启定时任务
def start_schedule_task():
    print("start_schedule_task")
    global isKeepLive, thread
    isKeepLive = True
    if not thread.is_alive():
        thread = GetDataThread(name="get_data", id=1)
    thread.start()
    rootWindow.title("开播监控已经启动")


# 关闭定时任务
def stop_schedule_task():
    print("stop_schedule_task")
    global isKeepLive, autoTaskCount
    isKeepLive = False
    autoTaskCount = 0
    thread.join()
    rootWindow.title("看看谁在直播")
    update_label_text("自动执行已停止")


# 弹窗显示
def show_message_content(event):
    for item in treeView.selection():
        up_info = treeView.item(item, "values")
        messagebox.showinfo("直播房间号", up_info[4])


# 创建窗口载体
def create_window():
    rootWindow.title("看看谁在直播")
    rootWindow.geometry('420x260')
    rootWindow.bind("<Destroy>", rootWindow.destroy)
    rootWindow.protocol("WM_DELETE_WINDOW", destroy_window)
    create_menu()
    create_tree_view()
    label = Label(rootWindow, textvariable=labelText)
    # label.config(font=("Courier", 14))
    label.grid()
    rootWindow.mainloop()


# 创建选项卡
def create_menu():
    menubar = Menu(rootWindow)
    menubar.add_cascade(label='开启定时任务', command=start_schedule_task)
    menubar.add_cascade(label='停止定时任务', command=stop_schedule_task)
    menubar.add_cascade(label='刷新', command=get_data)
    rootWindow.config(menu=menubar)


# 创建列表视图
def create_tree_view():
    treeView.column('#0', width=70, anchor='center')
    treeView.column('#1', width=50, anchor='center')
    treeView.column('#1', width=50, anchor='center')
    treeView.column('#2', width=100, anchor='center')
    treeView.column('#3', width=100, anchor='center')
    treeView.column('#4', width=100, anchor='center')
    treeView.heading('#0', text='上播提醒')
    treeView.heading('#1', text='序号')
    treeView.heading('#2', text='up名称')
    treeView.heading('#3', text='uid/mid')
    treeView.heading('#4', text='是否直播中')
    treeView.bind("<Double-1>", show_message_content)


# 自定义弹窗
def create_pop_up_window(title, msg):
    pop_up_window = tkinter.Toplevel(rootWindow)
    pop_up_window.title(title)
    pop_up_window.geometry('220x80')
    msg_label = Label(pop_up_window, text=msg)
    btn_confirm = Button(pop_up_window, text="确认", command=pop_up_window.destroy)
    msg_label.pack()
    btn_confirm.pack()
    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS or winsound.SND_ASYNC)


# 更新列表视图
def insert_tree_view(up_info_list):
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
            treeView.insert('', 'end', iid=up_info['mid'], values=item)
            for checked in checkedList:
                if up_info['mid'] == checked:
                    treeView.change_state(item=up_info['mid'], state='checked')
            treeView.grid()
    else:
        treeView.insert('', 'end', values=['---', errorMsg, errorCode, ' ---- '])
        treeView.grid()


# 更新计数文本
def update_label_text(text):
    labelText.set(text)


# 清空列表视图
def clear_tree_view():
    global checkedList
    checkedList = treeView.get_checked()
    item_list = treeView.get_children()
    for item in item_list:
        treeView.delete(item)


# 查看是否已经上播并且进行提醒
def check_alert_state_and_pop(up_info_list):
    for checked in checkedList:
        up_info = get_item_from_list(checked, up_info_list)
        old_up_info = get_item_from_list(checked, oldUpInfoList)
        if up_info and old_up_info and up_info['is_on_streaming'] != old_up_info['is_on_streaming']:
            # 提醒上播
            if up_info['is_on_streaming']:
                create_pop_up_window('上播提醒', up_info['name'] + "上播了")
            # 提醒下播
            #     create_pop_up_window('下播提醒', up_info['name'] + "下播了")


# 查找元素
def get_item_from_list(mid, up_info_list) -> Optional[Any]:
    for up_info in up_info_list:
        if up_info['mid'] == mid:
            return up_info
    return None


# 关闭时停止全部任务
def destroy_window():
    stop_schedule_task()
    rootWindow.destroy()


# TEST
def test_insert():
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', 123])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', 123])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', 123])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', 123])
    treeView.grid()
def test_update():
    clear_tree_view()
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, '直播中', 123])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', 123])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', 123])
    treeView.insert('', 'end', values=[len(treeView.get_children()), errorMsg, errorCode, ' ---- ', 123])
    treeView.grid()


if __name__ == '__main__':
    create_window()
    # get_all_mids_str_from_file()
    # search_one_by_mid('117906')
    # str_l = list()
    # str_l.append("117906")
    # search_multi_by_mid(str_l)
    # create_pop_up_window("aaaa", "asdjkasdhaksdhaksdhaskdhkasdhlada")