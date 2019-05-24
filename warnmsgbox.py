#!/usr/bin/env python
#-*- coding:utf-8 -*-

import tkinter as tk

class WarnBox(object):
    def __init__(self):
        self.messagebox_exits = False
        self.RootWidth = 0
        self.RootHeight = 0
        self.Root_xoffset = 0
        self.Root_yoffset = 0
        
    def ShowMessageBox(self, scrrenid, msg):
    
        if self.messagebox_exits == True:
            return
    
        self.messagebox_exits = True
    
        scrrenid.update()
        sell_win_width = 200
        sell_win_height = 80
        self.Root_xoffset = scrrenid.winfo_x()
        self.Root_yoffset = scrrenid.winfo_y()
        child_width = ((self.RootWidth - sell_win_width) / 2) + self.Root_xoffset
        child_height = ((self.RootHeight - sell_win_height) / 2) + self.Root_yoffset
        size_str = '%dx%d+%d+%d' % (sell_win_width, sell_win_height, child_width, child_height)
    
        thisTop = tk.Toplevel(scrrenid)
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
      self.messagebox_exits = False
      screenid.destroy()
      
    def SetRootSize(self, width, height, xoffset, yoffset):
      self.RootWidth = width
      self.RootHeight = height
      self.Root_xoffset = xoffset
      self.Root_yoffset = yoffset
      