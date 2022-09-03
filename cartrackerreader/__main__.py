#! /usr/bin/env python3
from tkinter import *
import tkinter.messagebox as box
import tkinter.simpledialog as sbox
import tkinter.filedialog as fbox
from threading import Thread
import serial
import time
from pathlib import Path
from importlib.resources import files
import json
class ReaderWindow(Tk):
    starttoken = b'--StartSQL'
    endtoken = b'--EndSQL'
    def __init__(self):
        self.settingsitems = (
            ('Save path','savepath',self.set_savepath),
            ('Port','port',self.set_port),
            ('Baud rate','baud',self.set_baud),
            ('Buffer increment size','buffersize',self.set_buffersize),
            ('Serial timeout','timeout',self.set_timeout),
            ('Request delay time','delay',self.set_delay),
        )
        try:
            self.settings_path = files('cartrackerreader') / 'settings.json'
        except ModuleNotFoundError:
            self.settings_path = Path(__file__).parent / 'settings.json'
        self._run_read_thread = True
        try:
            f = self.settings_path.open()
            self.settings = json.load(f)
            f.close()
        except IOError:
            self.settings = {}
        super().__init__()
        self.title('Car Tracker Reader')
        self.resizable(0,0)
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        Label(self,text='Car Tracker Reader',font=('Segoe UI',24)).grid(row=1,column=1,columnspan=2)
        self.startbtn = Button(self,text='Start',command=self.start_read)
        self.statustext = Label(self)
        self.startbtn.grid(row=1,column=3)
        self.statustext.grid(row=2,column=1,columnspan=3,sticky='NSEW')
        self.buttons = []
        Label(self,text='Settings',font=('Segoe UI',16)).grid(row=3,column=1,columnspan=2)
        self.savebtn = Button(self,text='Save',command=self.save_settings,state=DISABLED)
        self.savebtn.grid(row=3,column=3)
        for i in range(len(self.settingsitems)):
            Label(self,text=self.settingsitems[i][0]).grid(row=i+4,column=1)
            btn = Button(self,text=self.settings.get(self.settingsitems[i][1],'(Not set)'),command=self.settingsitems[i][2])
            self.buttons.append(btn)
            btn.grid(row=i+4,column=2,columnspan=2,sticky='NSEW')
    def on_close(self):
        if self.savebtn.config()['state'][4] == NORMAL:
            response = box.askyesnocancel('Car Tracker Reader','Save settings before exiting?')
            if response:
                self.save_settings()
                self.destroy()
            elif response == False:
                self.destroy()
        else:
            self.destroy()
    def read_end(self):
        for button in self.buttons:
            button.config(state=NORMAL)
        self.startbtn.config(text='Start',command=self.start_read,state=NORMAL)
    def read(self):
        self.startbtn.config(text='Stop',command=self.stop_read)
        self.statustext.config(text='Opening port...')
        try:
            ser = serial.Serial(self.settings['port'],self.settings['baud'],timeout=self.settings['timeout'],write_timeout=self.settings['timeout'])
            self.statustext.config(text='Sending request...')
            time.sleep(self.settings['delay'])
            ser.write(b'r')
        except serial.SerialTimeoutException:
            self.statustext.config(text='Timed out when sending request')
            self.read_end()
            return
        except serial.SerialException:
            self.statustext.config(text='Error opening port')
            self.read_end()
            return
        self.statustext.config(text='Reading...')
        buffer = b''
        incoming = b''
        bytesread = 0
        buffersize = self.settings['buffersize']
        message = ''
        errors = False
        try:
            while self._run_read_thread:
                incoming = ser.read(buffersize)
                buffer += incoming
                if len(incoming) < buffersize:
                    break
                else:
                    bytesread += buffersize
                    self.statustext.config(text='Reading (%i bytes)' % bytesread)
        except serial.SerialException:
            message += "\nError while reading data"
            errors = True
        try:
            startindex = buffer.index(self.starttoken) + len(self.starttoken)
        except ValueError:
            startindex = 0
            message += '\nCouldn\'t find start token'
            errors = True
        try:
            endindex = buffer.index(self.endtoken)
        except ValueError:
            endindex = len(buffer)
            message += '\nCouldn\'t find end token'
            errors = True
        buffer = buffer[startindex:endindex].strip()
        if len(buffer) == 0:
            self.statustext.config(text='No data returned' + message)
        else:
            filename = 'TrackerData_%i.sql' % int(time.time())
            self.statustext.config(text='Wrote to file "' + filename + '"' + message)
            f = open(Path(self.settings.get('savepath')) / filename,'wb')
            f.write(buffer)
            f.close()
            if box.askyesno('Reading complete','Reading complete, would you like to delete the data on the Car Tracker?\n\n' + ('There have been errors in retrieving the data\n\n' if errors else '') + 'REMEMBER: This cannot be undone'):
                self.startbtn.config(state=DISABLED)
                try:
                    self.statustext.config(text='Sending request...')
                    ser.write(b'd')
                    self.statustext.config(text='Deleting...')
                    buffer = ser.read(buffersize)
                    if b'1' in buffer:
                        self.statustext.config(text='Deleted Car Tracker data')
                    else:
                        self.statustext.config(text='Deletion not confirmed by Car Tracker')
                except serial.SerialTimeoutException:
                    self.statustext.config(text='Timed out when sending request')
                except serial.SerialException:
                    self.statustext.config(text='Error sending request')
        self.read_end()
    def start_read(self):
        for item in self.settingsitems:
            if self.settings.get(item[1]) == None:
                box.showinfo('Car Tracker Reader','Please complete the settings before reading from a device')
                return
        if self.savebtn.config()['state'][4] == NORMAL: self.save_settings()
        for button in self.buttons:
            button.config(state=DISABLED)
        self._run_read_thread = True
        Thread(target=self.read,daemon=True).start()
    def stop_read(self):
        self.startbtn.config(text='Stopping',state=DISABLED)
        self._run_read_thread = False
    def save_settings(self):
        f = self.settings_path.open('w')
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
    def set_timeout(self):
        timeout = sbox.askinteger('Change serial timeout','Enter the new serial timeout, in seconds\nIt should be greater than 0 but less than 20')
        if timeout != None and 0 < timeout <= 20:
            self.settings['timeout'] = timeout
            self.buttons[4].config(text=str(timeout))
            self.savebtn.config(state=NORMAL)
    def set_delay(self):
        delay = sbox.askinteger('Change request delay time','Enter the new request delay time, in seconds\nIt should be at least 2')
        if delay != None and delay >= 2:
            self.settings['delay'] = delay
            self.buttons[5].config(text=str(delay))
            self.savebtn.config(state=NORMAL)
if __name__ == '__main__':
    ReaderWindow().mainloop()
