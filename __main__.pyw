#! /usr/bin/env python3
from tkinter import *
import tkinter.messagebox as box
import tkinter.simpledialog as sbox
import tkinter.filedialog as fbox
from threading import Thread
import serial
from datetime import datetime
import os.path
import json
class ThreadStopException(Exception):
    pass
class ReaderWindow(Tk):
    starttoken = b'--StartSQL'
    endtoken = b'--EndSQL'
    def __init__(self):
        settingsitems = (
            ('Save path','savepath',self.set_savepath),
            ('Port','port',self.set_port),
            ('Baud rate','baud',self.set_baud),
            ('Buffer increment size','buffersize',self.set_buffersize),
        )
        self.read_thread = None
        self._run_read_thread = True
        try:
            f = open(os.path.join(os.path.dirname(__file__),"settings.json"),"r")
            self.settings = json.load(f)
            f.close()
        except IOError:
            self.settings = {}
        super().__init__()
        self.title('Car Tracker Reader')
        self.resizable(0,0)
        Label(self,text='Car Tracker Reader',font=('Segoe UI',16)).grid(row=1,column=1,columnspan=2)
        self.startbtn = Button(self,text='Start',command=self.start_read)
        self.statustext = Label(self)
        self.startbtn.grid(row=1,column=3)
        self.statustext.grid(row=2,column=1,columnspan=3,sticky='NSEW')
        self.buttons = []
        Label(self,text='Settings',font=('Segoe UI',16)).grid(row=3,column=1,columnspan=2)
        self.savebtn = Button(self,text='Save',command=self.save_settings,state=DISABLED)
        self.savebtn.grid(row=3,column=3)
        for i in range(len(settingsitems)):
            Label(self,text=settingsitems[i][0]).grid(row=i+4,column=1)
            btn = Button(self,text=self.settings.get(settingsitems[i][1],'(Not set)'),command=settingsitems[i][2])
            self.buttons.append(btn)
            btn.grid(row=i+4,column=2,columnspan=2,sticky='NSEW')
    def read(self):
        self.startbtn.config(text='Stop',command=self.stop_read)
        self.statustext.config(text='Opening port...')
        ser = serial.Serial(self.settings['port'],self.settings['baud'],timeout=5)
        self.statustext.config(text='Reading...')
        buffer = b''
        bytesread = 0
        buffersize = self.settings['buffersize']
        try:
            while self._run_read_thread:
                buffer += ser.read(buffersize)
                if self.endtoken in buffer:
                    break
                else:
                    bytesread += 100
                    self.statustext.config(text='Reading (%i bytes)' % bytesread)
        except serial.SerialException:
            pass
        ser.close()
        try:
            startindex = buffer.index(self.starttoken) + len(self.starttoken)
        except ValueError:
            startindex = 0
        try:
            endindex = buffer.index(self.endtoken)
        except ValueError:
            endindex = len(buffer)
        filename = 'TrackerData_%i.sql' % int(datetime.now().timestamp())
        f = open(os.path.join(self.settings.get('savepath'),filename),'wb')
        f.write(buffer[startindex:endindex])
        f.close()
        self.statustext.config(text='Closed port and wrote to file "%s"' % filename)
        self.startbtn.config(text='Start',command=self.start_read,state=NORMAL)
    def start_read(self):
        for key in ('savepath','port','baud','buffersize'):
            if self.settings.get(key) == None:
                box.showinfo('Car Tracker Reader','Please complete the settings before reading from a device')
                return
        if self.savebtn.config()['state'] == NORMAL: self.save_settings()
        self._run_read_thread = True
        self.read_thread = Thread(target=self.read,daemon=True)
        self.read_thread.start()
    def stop_read(self):
        self.startbtn.config(text='Stopping',state=DISABLED)
        self._run_read_thread = False
    def save_settings(self):
        f = open(os.path.join(os.path.dirname(__file__),"settings.json"),"w")
        json.dump(self.settings,f)
        f.close()
        self.savebtn.config(state=DISABLED)
    def set_savepath(self):
        savepath = fbox.askdirectory(initialdir=self.settings.get('savepath'),title='Choose save path')
        if savepath != None and savepath != '':
            self.settings['savepath'] = savepath
            self.buttons[0].config(text=savepath)
            self.savebtn.config(state=NORMAL)
    def set_port(self):
        port = sbox.askstring('Change port','Enter the serial port of the tracker device')
        if port != None and port != '':
            self.settings['port'] = port
            self.buttons[1].config(text=port)
            self.savebtn.config(state=NORMAL)
    def set_baud(self):
        baud = sbox.askinteger('Change baud rate','Enter the serial baud rate of the tracker device')
        if baud != None and baud > 0:
            self.settings['baud'] = baud
            self.buttons[2].config(text=str(baud))
            self.savebtn.config(state=NORMAL)
    def set_buffersize(self):
        size = sbox.askinteger('Change buffer increment size','Enter the number of bytes the PC will read from the serial buffer at once')
        if size != None and size > 0:
            self.settings['buffersize'] = size
            self.buttons[3].config(text=str(size))
            self.savebtn.config(state=NORMAL)
if __name__ == '__main__':
    ReaderWindow().mainloop()
