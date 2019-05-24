#!/usr/bin/env python
#-*- coding:utf-8 -*-

import serial
import threading
import time
import select
import sys
import queue
import serial.tools.list_ports as port_list
import operator
import crc

serial_name = None
serial_baud = None
serial_databits = None
serial_stopbits = None
serial_parity = None
serial_fd = None

def getDevList():
    return list(port_list.comports())

def getSerialName(name):
    global serial_name
    name_list = name.split(' - ')
    serial_name = name_list[0]
    print(serial_name)

def getSerialBaud(baud):
    global serial_baud
    serial_baud = int(baud, 10)
    print(serial_baud)
    
def getSerialDatabits(dbits):
    global serial_databits
    serial_databits = int(dbits, 10)
    print(serial_databits)
    
def getSerialStopbits(sbits):
    global serial_stopbits
    serial_stopbits = int(sbits, 10)
    print(serial_stopbits)
    
def getSerialParity(parity):
    global serial_parity
    ret = ''
    if operator.eq(parity, 'NONE'):
      ret = serial.PARITY_NONE
    elif operator.eq(parity, 'ODD'):
      ret = serial.PARITY_ODD
    elif operator.eq(parity, 'EVEN'):
      ret = serial.PARITY_EVEN
    else:
      print('Parity Error')
    serial_parity = ret
    print(serial_parity)

def open():
    global serial_fd 
    global serial_name
    global serial_baud 
    global serial_parity
    global serial_databits
    global serial_stopbits
    name = serial_name
    baud = serial_baud
    parity = serial_parity
    dbits = serial_databits
    sbits = serial_stopbits
    ret = False
    if serial_fd:
      print('serial already open')
      return
    try:
      serial_fd = serial.Serial(name, baudrate=baud, bytesize=dbits, parity=parity, stopbits=sbits, timeout=1)
      #self.serial = serial.Serial(name, baudrate=baud, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
      print(serial_fd)
      ret = True
    except Exception as e:
      print('open serial failed')
      print(e.args)
    finally:
      return ret

def close():
    global serial_fd
    if not serial_fd:
      return
    serial_fd.close()
    serial_fd = None
    
def send(msgid, msgcmd, msgpar, msgidentify):
    global serial_fd
    if not serial_fd:
       return
    
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
        serial_fd.write(bytes([val]))
    print(" ")
    serial_fd.flush()
  
def serial_data_process(serial):
    inputs = [serial,]
    outputs = []
    msglen = 0
    ch_list = []
    timeout_count = 0
    message_queue = {}
    message_queue[serial] = queue.queue()
    recv_count = 0
    all_count = 0

    while True:
        readable,writeable,exceptional = select.select(inputs, outputs, inputs, 1)
        if not (readable or writeable or exceptional):
            continue
        for r in readable:
            ch = r.read(1).encode('hex')
            if ch == 'a5':
                msglen = 1 
            if msglen > 0:
                ch_list.append(ch)
                msglen = msglen + 1 
            if msglen == 14: 
                msglen = 0
                timeout_count = 0
                print(time.strftime('%H:%M:%S',time.localtime(time.time())), end=' ')
                for val in ch_list:
                    print(val, end=' '),
                print('lost:', end= ' '),
                print(all_count - recv_count)
                recv_count = recv_count + 1
                all_count = all_count + 1
                ch_list = []
        for w in writeable:
            try:
                msg = message_queue[w].get_nowait()
            except Queue.Empty:
                outputs.remove(w)
            except Exception as e:
                print(e.args)
                if w in outputs:
                    outputs.remove(w)
            else:
                try:
                    send_id = msg[0]
                    send_cmd = msg[1]
                    send_buff = calc_senddata(send_id, send_cmd)
                    print('serial send:', end = ' ')
                    for val in send_buff:
                        print(hex(val), end=' ')
                        w.write(bytes([val]))
                    print(" ")
                    outputs.remove(w)
                except Exception as e:
                    print(e.args)


if __name__ == '__main__':
    serial_data_process(serial)
