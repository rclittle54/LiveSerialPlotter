#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 11:42:26 2019

Live Serial Plotter

@author: ryanlittle
"""

from tkinter import Tk, Label, StringVar, Entry, Button, OptionMenu, IntVar, Checkbutton, _setit
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import datetime
import serial
import numpy as np
import glob
import time


NPOINTS = 10000 # Number of points to store
MAXINPUTS = 5
TIMEDELAY = 10 # Milliseconds
PLOTRATIO = (5.82,3)
PLOTDPI = 100

PRINTDEBUG = False

def FindAllSerialPorts():
    if PRINTDEBUG: print("\t- Finding all serial ports")
    
    ports = glob.glob('/dev/cu.*')
    
    if PRINTDEBUG: print("\t\t- Finished globbing, checking ports")
    
    exclusionlist = ['/dev/cu.RyansPowerbeats3-SPPSer',
                     '/dev/cu.RyansPowerbeats3-Wirele-1',
                     '/dev/cu.Maker-1F97-RN-iAP-2',
                     '/dev/cu.RyansPowerbeats3-Wirele',
                     '/dev/cu.RyansPowerbeats3-SPPSer-1']
    result = []
    counter = 0
    for port in ports:
        if port in exclusionlist:
            continue
        counter += 1
        if PRINTDEBUG: print("\t\t\t- Checking #%d: %s"%(counter,port))
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except(OSError, serial.SerialException):
            pass
    return result

        

class PlotterWindow():
    def __init__(self,master):
        if PRINTDEBUG: print("\t- Top of init")
        self.master = master
        master.title("Live Serial Plotter")
        self.master.bind("<Configure>",self.resize)
        
        self.ser = None
        self.IS_SERIAL_CONNECTED = False
        
        self.serial_data = [[0 for i in range(MAXINPUTS)] for i in range(NPOINTS)]
        self.serial_plotline = []
        
        
        # Configuring to allow expansion
        for i in range(4):
            self.master.columnconfigure(i,weight=1)
            
        for i in range(5):
            self.master.rowconfigure(i,weight=1)
        
        
        
        #self.derivative_data = [0 for i in range(NPOINTS)]
        #self.derivative_plotline = []
        if PRINTDEBUG: print("\t- Loading figures")
        # Figure
        LCOL = 0
        #RCOL = 0
        self.f1 = plt.figure(figsize=PLOTRATIO,dpi=PLOTDPI)
        self.a1 = self.f1.add_subplot(111)
        self.a1.grid()
        self.a1.set_title("Serial Values")
        self.canvas1 = FigureCanvasTkAgg(self.f1,master)
        self.canvas1.get_tk_widget().grid(sticky='W',row=0,column=LCOL+0,columnspan=5)
        
        if PRINTDEBUG: print("\t- Loading labels")
        # Labels
        self.npointslabel = Label(master,text='# Points')
        self.npointslabel.grid(row=1,column=0,sticky='W')
        
        self.baudratelabel = Label(master,text="Baud Rate")
        self.baudratelabel.grid(row=2,column=0,sticky='W')
        
        self.portlabel = Label(master,text='Serial Port')
        self.portlabel.grid(row=3,column=0,sticky='W')
        
        self.serialconnectedstringvar = StringVar(master,value='Unconnected')
        self.serialconnectedlabel = Label(master,textvar=self.serialconnectedstringvar,fg='red',width=15)
        self.serialconnectedlabel.grid(row=1,column=3,sticky='W')
       
        self.numinputslabel = Label(master,text="# Inputs")
        self.numinputslabel.grid(row=4,column=0,sticky='W')
        
        if PRINTDEBUG: print("\t- Loading optionmenu lists")
        # OptionMenu lists
        _npoints_list = [10,25,50,75,100,250,500,750,1000]
        #_npoints_list = [25,50,100,250,500,1000]
        npoints_list = [str(x) for x in _npoints_list]
        available_ports = FindAllSerialPorts()
        _baud_rates = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000]
        baud_rates = [str(x) for x in _baud_rates]
        input_num_options = [str(x) for x in range(1,MAXINPUTS+1)]
        
        plotmethods = ['Markers only','Line only','Both']
        
        if PRINTDEBUG: print("\t- Loading stringvars")
        # StringVars
        self.npointsentrystr = StringVar(master,value="250")
        self.baudrateentrystr = StringVar(master,value="115200")
        self.portentrystr = StringVar(master,value=available_ports[-1])
        self.plotmethodentrystr = StringVar(master,value=plotmethods[1])
        self.numinputsentrystr = StringVar(master,value="1")
        
        
        if PRINTDEBUG: print("\t- Loading optionmenus")
        # Using OptionMenu instead:
        self.plotmethodoptionmenu = OptionMenu(master,self.plotmethodentrystr,*plotmethods)
        self.plotmethodoptionmenu.grid(row=4,column=2)
        
        self.npointsoptionmenu = OptionMenu(master,self.npointsentrystr,*npoints_list)
        self.npointsoptionmenu.grid(row=1,column=1,sticky='W')
        
        self.baudrateoptionmenu = OptionMenu(master,self.baudrateentrystr,*baud_rates)
        self.baudrateoptionmenu.grid(row=2,column=1,sticky='W')
        
        self.portoptionmenu = OptionMenu(master,self.portentrystr,*available_ports)
        self.portoptionmenu.width=20
        self.portoptionmenu.grid(row=3,column=1,sticky='W')
        
        self.numinputsoptionmenu = OptionMenu(master,self.numinputsentrystr,*input_num_options)
        self.numinputsoptionmenu.grid(row=4,column=1,sticky='W')
        
        
        if PRINTDEBUG: print("\t- Loading buttons")
        # Buttons
#        self.show_plot_line = IntVar(master,value=1)
#        self.showplotlinecheckbutton = Checkbutton(master,text='Show line',variable=self.show_plot_line,onvalue=1,offvalue=0)
#        self.showplotlinecheckbutton.grid(row=1,column=2)
        
        self.show_x_axis = IntVar(master,value=0)
        self.showxaxischeckbutton = Checkbutton(master,text='Show y=0',variable=self.show_x_axis,onvalue=1,offvalue=0)
        self.showxaxischeckbutton.grid(row=1,column=2)
        
#        self.clearplotbutton = Button(master,text='Clear Plot',command=self.ClearPlotWindow)
#        self.clearplotbutton.grid(row=3,column=2)
#        
        self.plotderivative = IntVar(master,value=0)
#        self.plotderivativecheckbutton = Checkbutton(master,text='Plot derivative', variable=self.plotderivative,onvalue=1,offvalue=0)
#        self.plotderivativecheckbutton.grid(row=2,column=2)
        
        self.connectbutton = Button(master,text='Connect',command=self.ConnectToSerial)
        self.connectbutton.grid(row=2,column=3)
        
        self.disconnectbutton = Button(master,text='Disconnect',command=self.DisconnectFromSerial)
        self.disconnectbutton.grid(row=3,column=3)
        
        self.refreshserialbutton = Button(master,text='Refresh Ports',command=self.RefreshSerial)
        self.refreshserialbutton.grid(row=3,column=2)
        
        
        self.exportdatabutton = Button(master,text='Export',command=self.ExportData)
        self.exportdatabutton.grid(row=4,column=3)
        
        self.printrawdata = IntVar(master,value=0)
        self.printrawbutton = Checkbutton(master,text='Print raw data',variable=self.printrawdata,onvalue=1,offvalue=0)
        self.printrawbutton.grid(row=2,column=2)
        
        if PRINTDEBUG: print("\t- Bottom of init")
        
        
        
    def mainloop(self):
        self.master.mainloop()
        return
    
    
    def resize(self,event):
        w = self.master.winfo_width()
        h = self.master.winfo_height()
        neww = (w-20)/100
        newh = (h-96)/100
        print(self.f1.get_size_inches()*self.f1.dpi)
        self.f1.set_size_inches(neww,newh)
        self.canvas1.draw()
        
        return
    
    
    
    def ConnectToSerial(self):
        try:
            port = self.portentrystr.get()
            baudrate = int(self.baudrateentrystr.get())
            print("Trying to connect to %s at %d"%(port,baudrate))
            self.ser = serial.Serial(port,baudrate)
            self.ser.flushInput()
            
            
        except:
            print("Error")
            self.ToggleSerialConnectedLabel(False)
            return -1
        
        print("Success.")
        
        self.IS_SERIAL_CONNECTED = True
        self.ToggleSerialConnectedLabel(True)
        self.GetSerialValue()
        
        
        return
    
    
    
    def DisconnectFromSerial(self):
        self.ser.close()
        self.ToggleSerialConnectedLabel(False)
        self.IS_SERIAL_CONNECTED = False
        return

    def ClearPlotWindow(self):
        ylim = self.a1.get_ylim()
        xlim = self.a1.get_xlim()
        self.a1.clear()
        self.a1.grid()
        self.a1.set_ylim(ylim)
        self.a1.set_xlim(xlim)
        self.canvas1.draw()
        return
        
    
    def RefreshSerial(self):
        new_serial_list = FindAllSerialPorts()
        #cgi = self.portoptionmenu.grid_info() # "Current Grid Info"
        #R,C = cgi['row'], cgi['column']
        
        print("Refreshing serial port list:")
        print(new_serial_list)
        
        # Set the variable to none
        self.portentrystr.set(new_serial_list[-1])
        
        # Delete the old list
        self.portoptionmenu['menu'].delete(0,'end')
        
        # Refresh:
        for port in new_serial_list:
            self.portoptionmenu['menu'].add_command(label=port, command=_setit(self.portentrystr,port))
            
        return
    
    def ExportData(self):
        
        timestamp = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
        outfname = 'SessionLogs/SerialSessionLog_%s.csv'%(timestamp)
        try:
            hit_data_start = False
            f = open(outfname,'w')
            for sd in self.serial_data:
                
                # Check if we have data yet, don't start appending until that point
                if not hit_data_start:
                    if not any(sd):
                        continue # Skip to the next data point if all values are zeros
                    else:
                        hit_data_start = True
                    
                wstr = ''
                for d in sd:
                    wstr += '%f,'%(d)
                wstr = wstr[:-1] +'\n'
                f.write(wstr)
                
                
            f.close()
            print("Successfully exported to %s"%(outfname))
        except:
            print("Error: Unable to export data")
        return


    def GetSerialValue(self):
        if not self.IS_SERIAL_CONNECTED:
            return
        
        try:
            # Read data
            rawdata = self.ser.readline().decode('utf8')
            self.ser.flushInput()
            self.ser.flushOutput()
            
            # Parse data
            x_nonewline = rawdata[:-1] # Ignore the trailing newline
            if self.printrawdata.get():
                print(x_nonewline)
            
            if ">" in x_nonewline and "<" in x_nonewline:
                x = x_nonewline[1:-2]
                try:
                    npoints = int(self.npointsentrystr.get())
                    #ninputs = int(self.numinputsentrystr.get())
                    x_split = x.split(' ')
                    
                    #x1 = float(x)
                    #self.serial_data.append(x1)
                    """
                    xdata = []
                    for i in range(max(ninputs,len(x_split))):
                        xdata.append(float(x_split[i]))
                    """
                    
                    # Make sure that every data package is the same length, so it's not a sequence
                    senddata = []
                    for i in range(MAXINPUTS):
                        try:
                            senddata.append(float(x_split[i]))
                        except:
                            senddata.append(self.serial_data[-1][i]) # Append the most recent value
                    
                    
                    
                    self.serial_data.append(senddata)
                    
                    self.serial_data = self.serial_data[1:]
                    self.serial_plotline = self.serial_data[-npoints:]
                    
                    #d = x1-self.serial_data[-2]
                    #self.derivative_data.append(d)
                    #self.derivative_line = self.derivative_data[-npoints:]
                    
                    #if np.abs(d) >= 0.5:
                    #    print(d)
                    
                    
                    self.master.after_idle(self.Plotline)
                
                
                except ValueError:
                    print("Invalid serial value: Non-floating point detected: %s"%(x))
            
            
        except Exception as e:
            print("Error in GetSerialValue()",e)
            
        self.master.after(TIMEDELAY,self.GetSerialValue)
        return
    
    
    
    def Plotline(self):
        
        numpoints = int(self.npointsentrystr.get())
        numinputs = int(self.numinputsentrystr.get())
        
        if self.plotmethodentrystr.get() == 'Markers only':
            plotmethod = '.'
        elif self.plotmethodentrystr.get() == 'Line only':
            plotmethod = '-'
        else:
            plotmethod = '.-'
        self.a1.clear()   
        
        
        for i in range(numinputs):
            plotline = [x[i] for x in self.serial_plotline]
            self.a1.plot(plotline,plotmethod,label=str(i))
        
        
            
        self.a1.grid()
        #self.a1.set_ylim(10,20)
        if self.show_x_axis.get():
            self.a1.set_ylim(0,1.125*np.amax(np.array(self.serial_data)))
        
        
        #ticklabels = [str(x) for x in np.linspace((1)*numpoints/10,0,10)]
        ticklabels = np.linspace(numpoints/10,0,5)
        #self.a1.set_xticks(np.linspace(0,numpoints,5),ticklabels)
        #self.a1.set_xticklabels(ticklabels)
        self.a1.set(xticks=np.linspace(0,numpoints,5),xticklabels=ticklabels)
        self.a1.set_xlabel("Time (s)")
        self.a1.set_ylabel("Serial Value")
        self.a1.legend(loc=3)
        
        
            
        self.canvas1.draw()
        return
    
    
    
    def ToggleSerialConnectedLabel(self,connection):
        if connection:
            self.serialconnectedstringvar.set('Connected')
            self.serialconnectedlabel.config(fg='green')
        else:
            self.serialconnectedstringvar.set('Unconnected')
            self.serialconnectedlabel.config(fg='red')
        return





if __name__ == "__main__":
    print("> Running.\t\t- %s"%(time.strftime("%H:%M:%S")))
    root = Tk()
    print("> Root initialized.\t- %s"%(time.strftime("%H:%M:%S")))
    useGUI = PlotterWindow(root)
    print("> GUI initialized.\t- %s"%(time.strftime("%H:%M:%S")))
    useGUI.mainloop()
    print("> Quitting.\t\t- %s"%(time.strftime("%H:%M:%S")))
    
    





