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
import select
import sys
import socket
import operator

import mySerial
import warnmsgbox

# 登陆功能 https://www.cnblogs.com/wwf828/p/7418181.html#autoid-15-0-0
# py3.7 MySQLdb https://www.cnblogs.com/SH170706/p/10082987.html, https://pypi.org/project/mysqlclient/#files
class Windows(object):
    def __init__(self):
        # 创建主窗口,用于容纳其它组件
        self.root = tk.Tk()
        # 给主窗口设置标题内容
        self.root.update()
        self.RootWidth = self.root.winfo_screenwidth() * 3 / 5
        self.RootHeight = self.root.winfo_screenheight() * 2 / 5
        self.Root_xoffset = self.root.winfo_x()
        self.Root_yoffset = self.root.winfo_y()
        
        self.serial = None
        self.messagebox_exits = False
        self.warn = warnmsgbox.WarnBox()
        self.warn.SetRootSize(self.RootWidth, self.RootHeight, self.Root_xoffset, self.Root_yoffset)
  
        self.root.title('地锁串口工具')
        set_screen_string = "%dx%d" % (self.RootWidth, self.RootHeight)
        self.root.geometry(set_screen_string)
        self.root.resizable(width=False, height=False)

        combox_value_list = mySerial.getDevList()
        for p in combox_value_list:
          print(p)
          
        self.serialport_label = tk.Label(self.root, text='Serial Port')
        self.serialport_combox = ttk.Combobox(self.root, values=combox_value_list)
        self.serialport_combox.bind("<<ComboboxSelected>>", self.select_serial_port)
        
        combox_baud_list = [4800, 9600, 19200, 38400, 57600, 115200]
        self.serialbaud_label = tk.Label(self.root, text='Serial Baud')
        self.serialbaud_combox = ttk.Combobox(self.root, values=combox_baud_list)
        self.serialbaud_combox.bind("<<ComboboxSelected>>", self.select_serial_baud)
        
        combox_databits_list = [5, 6, 7, 8]
        self.serialdbit_label = tk.Label(self.root, text='Serial DataBits')
        self.serialdbit_combox = ttk.Combobox(self.root, values=combox_databits_list)
        self.serialdbit_combox.bind("<<ComboboxSelected>>", self.select_serial_dbit)
        
        combox_parity_list = ['NONE', 'ODD', 'EVEN']
        self.serialpari_label = tk.Label(self.root, text='Serial Parity')
        self.serialpari_combox = ttk.Combobox(self.root, values=combox_parity_list)
        self.serialpari_combox.bind("<<ComboboxSelected>>", self.select_serial_parity)
        
        combox_stopbits_list = [1, 1.5, 2]
        self.serialsbit_label = tk.Label(self.root, text='Serial StopBits')
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
        clos = ('DeviceID', 'Status', 'CMD', 'CmdStatus', 'Beep','Battery','HaveCar','UltraSafeDistance','UltraCheckTime','UltraCheckDistance','HeartTime')
        self.display_info = ttk.Treeview(self.root, columns=clos, show='headings')
        for col in clos:
            self.display_info.heading(col, text=col)
        # 设置列的宽度和对齐方式
        self.display_info.column('0', width=50, anchor='center')
        self.display_info.column('1', width=30, anchor='center')
        self.display_info.column('2', width=20, anchor='center')
        self.display_info.column('3', width=50, anchor='center')
        self.display_info.column('4', width=30, anchor='center')
        self.display_info.column('5', width=40, anchor='center')
        self.display_info.column('6', width=40, anchor='center')
        self.display_info.column('7', width=60, anchor='center')
        self.display_info.column('8', width=60, anchor='center')
        self.display_info.column('9', width=60, anchor='center')
        self.display_info.column('10', width=60, anchor='center')
        
        # 创建刷新显示的线程
        t1 = threading.Thread(target=self.ThreadUpdateDisplay, args=())
        t1.setDaemon(True)
        t1.start()
        
    #获取串口名
    def select_serial_port(self, args):
       name = self.serialport_combox.get()
       mySerial.getSerialName(name)
      
    #获取波特率
    def select_serial_baud(self, args):
      baud = self.serialbaud_combox.get()
      mySerial.getSerialBaud(baud)

    #获取数据位 
    def select_serial_dbit(self, args):
      dbits = self.serialdbit_combox.get()
      mySerial.getSerialDatabits(dbits)
      
    #获取校验位
    def select_serial_parity(self, args):
      parity = self.serialpari_combox.get()
      mySerial.getSerialParity(parity)

    #获取停止位  
    def select_serial_stopbits(self, args):
      sbits = self.serialsbit_combox.get()
      mySerial.getSerialStopbits(sbits)
      
    def serial_open(self):
      if mySerial.open():
        mySerial.StartRecvice()
        self.sendbox_devid_label.__setitem__('state', 'normal')
        self.sendbox_devid_entry.__setitem__('state', 'normal')
        self.sendbox_cmd_label.__setitem__('state', 'normal')
        self.sendbox_cmd_entry.__setitem__('state', 'normal')
        self.sendbox_para_label.__setitem__('state', 'normal')
        self.sendbox_para_entry.__setitem__('state', 'normal')
        self.sendbox_identify_label.__setitem__('state', 'normal')
        self.sendbox_identify_entry.__setitem__('state', 'normal')
        self.sendbox_button.__setitem__('state', 'normal')
      else:
        print('open serial failed')
        
    def serial_close(self):
      mySerial.close()
      self.sendbox_devid_label.__setitem__('state', 'disabled')
      self.sendbox_devid_entry.__setitem__('state', 'disabled')
      self.sendbox_cmd_label.__setitem__('state', 'disabled')
      self.sendbox_cmd_entry.__setitem__('state', 'disabled')
      self.sendbox_para_label.__setitem__('state', 'disabled')
      self.sendbox_para_entry.__setitem__('state', 'disabled')
      self.sendbox_identify_label.__setitem__('state', 'disabled')
      self.sendbox_identify_entry.__setitem__('state', 'disabled')
      self.sendbox_button.__setitem__('state', 'disabled')
      
    def serial_send(self):
      msgid = None
      msgcmd = None
      msgpar = None
      msgidentify = None
      try:
        msgid = int(self.sendbox_devid_entry.get(), 16)
        msgcmd = int(self.sendbox_cmd_entry.get(), 16)
      except:
        print("id and cmd must valid number")
        self.warn.ShowMessageBox(self.root, "id和cmd不能空")
        return
    
      try:
        msgpar = int(self.sendbox_para_entry.get(), 10)
        msgidentify = int(self.sendbox_identify_entry.get(), 10)
      except:
        if not msgpar:
          msgpar = 0
        if not msgidentify:
          msgidentify = 0xFFFFFFFF
          
      mySerial.send(msgid, msgcmd, msgpar, msgidentify)
      
    def ThreadUpdateDisplay(self):
        socketid = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ipport = ('127.0.0.1', 9876)
        socketid.bind(ipport)
        socketid.listen(5)
        
        display_len = 0
        display_list_info = []
        ret_list = []
        inputs = [socketid, ]
        outputs = []
        while True:
            display_list_info = []
            readable,writeable,exceptional = select.select(inputs, outputs, inputs, 0)
            if not readable:
              continue
            for r in readable:
              if r is socketid:
                conn,addr = r.accept()
                print('new connect')
                conn.setblocking(False)
                inputs.append(conn)
              else:
                try:
                  recv_bytes = r.recv(1024)
                except:
                  print('recv except')
                else:
                  if recv_bytes:
                    recv_string = str(recv_bytes, encoding='utf-8')
                    print('recv:%s' % recv_string)
                    recv_list = recv_string.split('-')
                    mType = recv_list[0]
                    if mType == 'Ctrl':
                      mId = recv_list[1]
                      mCmd = recv_list[2]
                      mParamter = recv_list[3]
                      mIdentify = recv_list[4]
                      item = [mId, 0, mCmd, 0, 0, mIdentify]
                      self.display_info.insert("", 0, values=item)
                    else: # 'Resp'
                      mId = recv_list[1]
                      mCmd = recv_list[2]
                      mResp = recv_list[3]
                      mIdentify = recv_list[4]
                      isInDisplay = False
                      
                      item = []
                      alreadyExitsItem = self.display_info.get_children()
                      if alreadyExitsItem:
                        print('alreadyExitsItem')
                        for tmp in alreadyExitsItem:
                          item_id = self.display_info.set(tmp, column='DeviceID')
                          if operator.eq(item_id, mId):
                            #print('find same id')
                            item = tmp
                            isInDisplay = True
                            break
                      #print('one:')
                      #print(item)
                      if not item:
                        #print('add new item')
                        self.display_info.insert("", 'end', values=item)
                        itemtuple = self.display_info.get_children()
                        for tmp in itemtuple:
                          print(tmp)
                        item = tmp
                          
                      #print('two:')
                      #print(item)
                      #print(mCmd)
                      if mCmd in ['1', '2', '3', '102']:
                        #print('set cmd 123')
                        self.display_info.set(item, column='Status', value=mResp)
                        print(item)
                      elif mCmd in ['4','5','6']:
                        if mResp == '0':
                          self.display_info.set(item, column='Beep', value='On')
                        else:
                          self.display_info.set(item, column='Beep', value='Off')
                      elif mCmd in ['7', '101']:
                        self.display_info.set(item, column='Battery', value=mResp)
                      elif mCmd == 8:
                        if mResp == '0':
                          self.display_info.set(item, column='HaveCar', value='Y')
                        else:
                          self.display_info.set(item, column='HaveCar', value='N')
                      elif mCmd == '15':
                        resp = int(mResp, 16)
                        if (resp & 0xf0) == 0x10:
                          self.display_info.set(item, column='HaveCar', value='Y')
                        else:
                          self.display_info.set(item, column='HaveCar', value='N')
                        self.display_info.set(item, column='HaveCar', value=resp & 0x0f)
                      #elif mCmd in ['9', '10']:
                        
                      #elif mCmd in ['11', '12']:
                        
                      #elif mCmd == '14':
                        
                      #elif mCmd in ['16', '17']:
                      
                      
                      
                      if isInDisplay:
                        item_cmd = self.display_info.set(item, column='CMD')
                        if operator.eq(mCmd, item_cmd):
                          self.display_info.set(item, column='CmdStatus', value='OK')
                        else:
                          self.display_info.set(item, column='CmdStatus', value='ERR')
                      else:
                        self.display_info.set(item, column='DeviceID', value=mId)
                      self.display_info.set(item, column='CMD', value=mCmd)
                      #  print('add new item')
                      #  print(item)
                      #  self.display_info.insert("", 'end', values=item) #0添加到头部,'end'添加到尾部
                  else:
                    r.close()
                    print('client close')


    def test_input_is_digit(self, content):
        # 如果不加上==""的话，就会发现删不完。总会剩下一个数字
        rule = r"^[0-9]+\.?[0-9]?$"
        ret = re.match(rule, content)
        #print(content)
        if ret or content == "":
            # if content.isdigit() or content == "":
            #if int(content, 16) > 0xffff:
            #    self.ShowMessageBox('DeviceId Must Little 0xffff')
            return True
        else:
            #检测复合0x1 0x12345678 格式的字符串,十六进制
            rule = r"^0x[0-9a-fA-F]*$"
            ret = re.match(rule, content)
            if ret or content == "":
              return True
            else:
              self.warn.ShowMessageBox(self.root, '只能够输入数字')
              return False


    # 完成布局
    def gui_arrang(self):
        self.serialport_label.grid(row=0, column=0, padx=1, pady=1)
        self.serialport_combox.grid(row=0, column=1, padx=1, pady=1)
        self.serialport_combox.current(0)
        
        self.serialbaud_label.grid(row=1, column=0, padx=1, pady=1)
        self.serialbaud_combox.grid(row=1, column=1, padx=1, pady=1)
        self.serialbaud_combox.current(5)
        
        self.serialdbit_label.grid(row=2, column=0, padx=1, pady=1)
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
        
        #根据下拉列表内容初始化串口需要的变量
        self.select_serial_port(0)
        self.select_serial_baud(0)
        self.select_serial_dbit(0)
        self.select_serial_parity(0)  
        self.select_serial_stopbits(0)
        
        display_start_x = 300
        display_start_y = 2
        # 两侧留出20空余空间
        display_width = self.RootWidth - display_start_x - 40;
        # 底部留出20空余空间
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