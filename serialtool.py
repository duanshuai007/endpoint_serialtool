#!/usr/bin/env python
# -*- coding:utf-8 -*-

# from tkinter import *
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkm
import time
import re
import threading
import xpinyin
import serial
import select
import sys
import crc
import serial.tools.list_ports as port_list

# 登陆功能 https://www.cnblogs.com/wwf828/p/7418181.html#autoid-15-0-0
# py3.7 MySQLdb https://www.cnblogs.com/SH170706/p/10082987.html, https://pypi.org/project/mysqlclient/#files
class Windows(object):
    def __init__(self):
        # 创建主窗口,用于容纳其它组件
        self.root = tk.Tk()
        # 给主窗口设置标题内容
        self.root.update()
        self.RootWidth = self.root.winfo_screenwidth() * 2 / 5
        self.RootHeight = self.root.winfo_screenheight() * 2 / 5
        self.Root_xoffset = self.root.winfo_x()
        self.Root_yoffset = self.root.winfo_y()
        
        self.serial = 0
        self.messagebox_exits = False
        self.serialname = ''
        self.serialbaud = 0
        self.serialparity = ''
        self.serialdatabits = 0
        self.serialstopbits = 0
        
        self.root.title('地锁串口工具')
        set_screen_string = "%dx%d" % (self.RootWidth, self.RootHeight)
        self.root.geometry(set_screen_string)
        self.root.resizable(width=False, height=False)

        combox_value_list = list(port_list.comports())
        for p in combox_value_list:
          print(p)
        self.serialport_label = tk.Label(self.root, text='Serial Port')
        #self.serialport_Entry = tk.Entry(self.root)
        self.serialport_combox = ttk.Combobox(self.root, values=combox_value_list)
        self.serialport_combox.bind("<<ComboboxSelected>>", self.select_serial_port)
        
        combox_baud_list = [4800, 9600, 19200, 38400, 57600, 115200]
        self.serialbaud_label = tk.Label(self.root, text='Serial Baud')
        #self.serialbaud_Entry = tk.Entry(self.root)
        self.serialbaud_combox = ttk.Combobox(self.root, values=combox_baud_list)
        self.serialbaud_combox.bind("<<ComboboxSelected>>", self.select_serial_baud)
        
        combox_databits_list = [5, 6, 7, 8]
        self.serialdbit_label = tk.Label(self.root, text='Serial DataBits')
        #self.serialdbit_Entry = tk.Entry(self.root)
        self.serialdbit_combox = ttk.Combobox(self.root, values=combox_databits_list)
        self.serialdbit_combox.bind("<<ComboboxSelected>>", self.select_serial_dbit)
        
        combox_parity_list = ['None', 'ODD', 'ENEV']
        self.serialpari_label = tk.Label(self.root, text='Serial Parity')
        #self.serialpari_Entry = tk.Entry(self.root)
        self.serialpari_combox = ttk.Combobox(self.root, values=combox_parity_list)
        self.serialpari_combox.bind("<<ComboboxSelected>>", self.select_serial_parity)
        
        combox_stopbits_list = [1, 1.5, 2]
        self.serialsbit_label = tk.Label(self.root, text='Serial StopBits')
        #self.serialsbit_Entry = tk.Entry(self.root)
        self.serialsbit_combox = ttk.Combobox(self.root, values=combox_stopbits_list)
        self.serialsbit_combox.bind("<<ComboboxSelected>>", self.select_serial_stopbits)
        
        self.serial_open_button = tk.Button(self.root, command=self.serial_open, text="open", bg='white', font=("黑体", 14))
        self.serial_close_button = tk.Button(self.root, command=self.serial_close, text="close", bg='white', font=("黑体", 14))
        
        test_cmd = self.root.register(self.test_input_is_digit)
                                          
        self.sendbox_devid_label = tk.Label(self.root, text='Device ID')
        self.sendbox_devid_entry = tk.Entry(self.root, validate='key', validatecommand=(test_cmd, '%P'))
        self.sendbox_cmd_label = tk.Label(self.root, text='Cmd')
        self.sendbox_cmd_entry = tk.Entry(self.root, validate='key', validatecommand=(test_cmd, '%P'))
        self.sendbox_para_label = tk.Label(self.root, text='paramter')
        self.sendbox_para_entry = tk.Entry(self.root, validate='key', validatecommand=(test_cmd, '%P'))
        self.sendbox_identify_label = tk.Label(self.root, text='identify')
        self.sendbox_identify_entry = tk.Entry(self.root, validate='key', validatecommand=(test_cmd, '%P'))
        self.sendbox_button = tk.Button(self.root, command=self.serial_send, text='send', bg='white', font=("黑体", 14))
        
        # 参考自https://cloud.tencent.com/developer/ask/130543
        # 参考自https://www.cnblogs.com/qwangxiao/p/9940972.html
        clos = ('DeviceID', 'Status', 'CMD', 'CmdStatus', 'yichang', 'online')
        self.display_info = ttk.Treeview(self.root, columns=clos, show='headings')
        for col in clos:
            self.display_info.heading(col, text=col)
            
        # 设置列的宽度和对齐方式
        self.display_info.column('0', width=60, anchor='center')
        self.display_info.column('1', width=60, anchor='center')
        self.display_info.column('2', width=60, anchor='center')
        self.display_info.column('3', width=60, anchor='center')
        self.display_info.column('4', width=60, anchor='center')
        self.display_info.column('5', width=60, anchor='center')


        # 创建刷新显示的线程
        t1 = threading.Thread(target=self.ThreadUpdateDisplay, args=())
        t1.setDaemon(True)
        t1.start()
        
    def select_serial_port(self, args):
      print(self.serialport_combox.get())
      name = self.serialport_combox.get()
      name_list = name.split(' - ')
      self.serialname = name_list[0]
      
    def select_serial_baud(self, args):
      print(self.serialbaud_combox.get())
      self.serialbaud = int(self.serialbaud_combox.get(), 10)
      
    def select_serial_dbit(self, args):
      print(self.serialdbit_combox.get())
      self.serialdatabits = int(self.serialdbit_combox.get(), 10)
      
    def select_serial_parity(self, args):
      print(self.serial_pari_combox.get())
      parity = self.serial_pari_combox.get()
      if parity == 'None':
        print('no parity')
        self.serialparity = 'N'
      elif parity == 'ODD':
        print('ODD parity')
      else :
        print('EVEN parity')
      
    def select_serial_stopbits(self, args):
      print(self.serialsbit_combox.get())  
      self.serialstopbits = int(self.serialsbit_combox.get(), 10)
      
    def ThreadUpdateDisplay(self):
        display_len = 0
        ret_list = []
        while True:
            display_list_info = []

            if ret_list:
                if len(ret_list) != display_len:
                    display_len = len(ret_list)
                    ret_list.sort(key=lambda e: e[1], reverse=True)
                    alreadyExitsItem = self.display_info.get_children()

                    for new_item in ret_list:  # 从数据库的数据中提取出一条信息
                        isInDisplay = False
                        new_item_name = '%s' % new_item[1]  # 获取名字信息
                        for item in alreadyExitsItem:  # 从显示列表中提取一条信息
                            item_text = self.display_info.item(item, "values")
                            # print(item_text[1])#输出所选行的第一列的值
                            item_name = '%s' % item_text[1]  # 获取显示的名字信息
                            result = cmp(item_name, new_item_name)
                            if result == 0:
                                isInDisplay = True
                                break
                        if isInDisplay == False:
                            display_list_info.append(new_item)
                            # 将获取到的商品名加入到goodsNameList中，不能重复加入，并将名称转换为拼音
                            unicode_name = u'%s' % new_item_name
                            # print unicode_name
                            name_pinyin = xpinyin.Pinyin().get_pinyin(unicode_name)
                            # print 'pinyin =%s' % ret
                            self.goodsNameList.append([new_item_name, name_pinyin])
                            # print self.goodsNameList

            # print display_list_info
            if display_list_info:
                for item in display_list_info:
                    self.display_info.insert("", "end", values=item)

            time.sleep(1)

    def serial_open(self):
        name = self.serialname
        if not name:
          tmpstring = self.serialport_combox.get()
          tmp_list = tmpstring.split(' - ')
          self.serialname = tmp_list[0]
          name = self.serialname
          
        baud = self.serialbaud
        if not baud:
          self.serialbaud = int(self.serialbaud_combox.get(), 10)
          baud = self.serialbaud
          
        dbits = self.serialdatabits
        if not dbits:
          self.serialdatabits = int(self.serialdbit_combox.get(), 10)
          dbits = self.serialdatabits
          
        parity = self.serialparity
        if not parity:
          parity_string = self.serialpari_combox.get()
          if parity_string == 'None':
            self.serialparity = 'N'
            parity = self.serialparity
            
        sbits = self.serialstopbits
        if not sbits:
          self.serialstopbits = int(self.serialsbit_combox.get(), 10)
          sbits = self.serialstopbits
          
        try:
          self.serial = serial.Serial(name, baudrate=baud, bytesize=dbits, parity=parity, stopbits=sbits, timeout=0)
          #self.serial = serial.Serial(name, baudrate=baud, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
          print(self.serial)
          #print('serial open: %s %s %s %s %s' % (name, baud, dbits, parity, sbits))

          self.sendbox_devid_label.__setitem__('state', 'normal')
          self.sendbox_devid_entry.__setitem__('state', 'normal')
          self.sendbox_cmd_label.__setitem__('state', 'normal')
          self.sendbox_cmd_entry.__setitem__('state', 'normal')
          self.sendbox_para_label.__setitem__('state', 'normal')
          self.sendbox_para_entry.__setitem__('state', 'normal')
          self.sendbox_identify_label.__setitem__('state', 'normal')
          self.sendbox_identify_entry.__setitem__('state', 'normal')
          self.sendbox_button.__setitem__('state', 'normal')
          
        except Exception as e:
          print('open serial failed')
          print(e.args)
          
    def serial_close(self):
        #name = self.serialport_Entry.get()
        self.serial.close()
        self.sendbox_devid_label.__setitem__('state', 'disabled')
        self.sendbox_devid_entry.__setitem__('state', 'disabled')
        self.sendbox_cmd_label.__setitem__('state', 'disabled')
        self.sendbox_cmd_entry.__setitem__('state', 'disabled')
        self.sendbox_para_label.__setitem__('state', 'disabled')
        self.sendbox_para_entry.__setitem__('state', 'disabled')
        self.sendbox_identify_label.__setitem__('state', 'disabled')
        self.sendbox_identify_entry.__setitem__('state', 'disabled')
        self.sendbox_button.__setitem__('state', 'disabled')
        
        #print('serial close %s' % name)
        
    def serial_send(self):
        
        msgid = int(self.sendbox_devid_entry.get(), 10)
        msgcmd = int(self.sendbox_cmd_entry.get(), 10)
        msgpar = int(self.sendbox_para_entry.get(), 10)
        msgidentify = int(self.sendbox_identify_entry.get(), 10)
        send_string = []
        send_head = []
        
        send_head.append((msgid >> 8) & 0xff)
        send_head.append(msgid & 0xff)
        send_head.append(msgid % 30)
        
        send_string.append(0xA5)
        send_string.append(0x0C)
        send_string.append(msgid & 0xff)
        send_string.append((msgid >> 8) & 0xff)
        send_string.append(msgcmd)
        send_string.append(msgidentify & 0xff)
        send_string.append((msgidentify >> 8) & 0xff)
        send_string.append((msgidentify >> 16) & 0xff)
        send_string.append((msgidentify >> 24) & 0xff)
        
        send_head.extend(send_string)
        
        crc_val = crc.calc_senddata(send_string)
        print(hex(crc_val))
        send_head.append(crc_val & 0xff)
        send_head.append((crc_val >> 8) & 0xff)
        send_head.append(0x5A)
        
        print('serial send:')
        for val in send_head:
            print(hex(val), end=' ')
            self.serial.write(bytes([val]))
        print(" ")
        self.serial.flush()
                        
    def ShowMessageBox(self, msg):

        if self.messagebox_exits == True:
            return

        self.messagebox_exits = True

        self.root.update()
        sell_win_width = 200
        sell_win_height = 80
        self.Root_xoffset = self.root.winfo_x()
        self.Root_yoffset = self.root.winfo_y()
        child_width = ((self.RootWidth - sell_win_width) / 2) + self.Root_xoffset
        child_height = ((self.RootHeight - sell_win_height) / 2) + self.Root_yoffset
        size_str = '%dx%d+%d+%d' % (sell_win_width, sell_win_height, child_width, child_height)

        thisTop = tk.Toplevel(self.root)
        thisTop.resizable(False, False)
        thisTop.geometry(size_str)
        thisTop.wm_attributes('-topmost', True)
        # 设置右上角的X功能
        thisTop.protocol("WM_DELETE_WINDOW", lambda arg=thisTop: self.FuncButtonCancel(arg))
        # 设置窗口始终在最上层
        # self.selltop.wm_attributes("-topmost", 1)
        thisTop.title('Warning')
        tk.Label(thisTop, text=msg, fg='red', bg='blue', font=('黑体', 18)).pack()
        tk.Button(thisTop, text='确认', font=('黑体', 14), command=lambda: self.FuncButtonCancel(thisTop)).pack()

    def FuncButtonCancel(self, screenid):
      screenid.destroy()
      
    def test_input_is_digit(self, content):
        # 如果不加上==""的话，就会发现删不完。总会剩下一个数字
        rule = r"^[0-9]+\.?[0-9]?$"
        ret = re.match(rule, content)

        if ret or content == "":
            # if content.isdigit() or content == "":
            #if int(content, 16) > 0xffff:
            #    self.ShowMessageBox('DeviceId Must Little 0xffff')
            return True
        else:
            # tkm.showwarning('警告','只能够输入数字')
            self.ShowMessageBox('只能够输入数字')
            # print content
            return False

    # 完成布局
    def gui_arrang(self):
        self.serialport_label.grid(row=0, column=0, padx=1, pady=1)
        #self.serialport_Entry.grid(row=0, column=1, padx=1, pady=1)
        self.serialport_combox.grid(row=0, column=1, padx=1, pady=1)
        self.serialport_combox.current(0)
        
        self.serialbaud_label.grid(row=1, column=0, padx=1, pady=1)
        #self.serialbaud_Entry.grid(row=1, column=1, padx=1, pady=1)
        self.serialbaud_combox.grid(row=1, column=1, padx=1, pady=1)
        self.serialbaud_combox.current(5)
        
        self.serialdbit_label.grid(row=2, column=0, padx=1, pady=1)
        #self.serialdbit_Entry.grid(row=2, column=1, padx=1, pady=1)
        self.serialdbit_combox.grid(row=2, column=1, padx=1, pady=1)
        self.serialdbit_combox.current(3)
        
        self.serialpari_label.grid(row=3, column=0, padx=1, pady=1)
        self.serialpari_combox.grid(row=3, column=1, padx=1, pady=1)
        self.serialpari_combox.current(0)
        
        self.serialsbit_label.grid(row=4, column=0, padx=1, pady=1)
        self.serialsbit_combox.grid(row=4, column=1, padx=1, pady=1)
        self.serialsbit_combox.current(0)
        
        self.serial_open_button.grid(row=5, column=0, padx=1, pady=1)
        self.serial_close_button.grid(row=5, column=1, padx=1, pady=1)
        
        self.sendbox_devid_label.grid(row=7, column=0, padx=1, pady=1)
        self.sendbox_devid_entry.grid(row=7, column=1, padx=1, pady=1)
        self.sendbox_cmd_label.grid(row=8, column=0, padx=1, pady=1)
        self.sendbox_cmd_entry.grid(row=8, column=1, padx=1, pady=1)
        self.sendbox_para_label.grid(row=9, column=0, padx=1, pady=1)
        self.sendbox_para_entry.grid(row=9, column=1, padx=1, pady=1)
        self.sendbox_identify_label.grid(row=10, column=0, padx=1, pady=1)
        self.sendbox_identify_entry.grid(row=10, column=1, padx=1, pady=1)
        self.sendbox_button.grid(row=11, column=1, padx=1, pady=1)
        
        self.sendbox_devid_label.__setitem__('state', 'disabled')
        self.sendbox_devid_entry.__setitem__('state', 'disabled')
        self.sendbox_cmd_label.__setitem__('state', 'disabled')
        self.sendbox_cmd_entry.__setitem__('state', 'disabled')
        self.sendbox_para_label.__setitem__('state', 'disabled')
        self.sendbox_para_entry.__setitem__('state', 'disabled')
        self.sendbox_identify_label.__setitem__('state', 'disabled')
        self.sendbox_identify_entry.__setitem__('state', 'disabled')
        self.sendbox_button.__setitem__('state', 'disabled')
        
        display_start_x = 300
        display_start_y = 2
        # 两侧留出20空余空间
        display_width = self.RootWidth - display_start_x - 40;
        # 底部留出200空余空间
        display_height = self.RootHeight - 20;
        self.display_info.place(x=display_start_x, y=display_start_y, width=display_width, height=display_height)

def main():
    # 初始化对象
    win = Windows()
    # 进行布局
    win.gui_arrang()
    # 主程序执行
    tk.mainloop()
    pass

if __name__ == "__main__":
    main()