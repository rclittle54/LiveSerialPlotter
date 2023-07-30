#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Tk code to plot live data
"""

from argparse import Namespace
import logging
import matplotlib

matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sys
from tkinter import Tk, Label, StringVar, Button, OptionMenu, IntVar, Checkbutton, _setit

from LiveDataSource import LiveDataSource

logger = logging.getLogger(__name__)

TIMEDELAY = 100  # Milliseconds between getting new data/updating plot
PLOTRATIO = (9, 6)
PLOTDPI = 100


# =============================================================================
# Main GUI window class.
class PlotterWindow:
    def __init__(self, master: Tk, args: Namespace):
        # Tkinter parts
        self.master = master
        self.master.title("Live Serial Plotter")
        self.master.resizable(False, False)  # Prevent resizing

        self.datasource = LiveDataSource(master, args)
        self.args = args

        # set up a close window handler
        master.protocol("WM_DELETE_WINDOW", self.die)

        # Figure
        self.f1 = plt.figure(figsize=PLOTRATIO, dpi=PLOTDPI)
        self.a1 = self.f1.add_subplot(111)
        self.a1.grid()
        self.a1.set_title("Serial Values")
        self.a1.set_xticklabels([])
        self.canvas1 = FigureCanvasTkAgg(self.f1, master)
        self.canvas1.get_tk_widget().grid(row=0, column=0, columnspan=6, pady=20)

        # Labels
        self.npointslabel = Label(master, text="# Points")
        self.npointslabel.grid(row=1, column=0, sticky="W")

        self.baudratelabel = Label(master, text="Baud Rate")
        self.baudratelabel.grid(row=2, column=0, sticky="W")

        self.portlabel = Label(master, text="Serial Port")
        self.portlabel.grid(row=3, column=0, sticky="W")

        self.serialconnectedstringvar = StringVar(master, value="Unconnected")
        self.serialconnectedlabel = Label(master, textvar=self.serialconnectedstringvar, fg="red", width=15)
        self.serialconnectedlabel.grid(row=1, column=3)

        self.numinputslabel = Label(master, text="# Inputs")
        self.numinputslabel.grid(row=4, column=0, sticky="W")

        self.currentvallabel = Label(master, text="Most recent:")
        self.currentvallabel.grid(row=1, column=5)

        self.currentvalstringvar = StringVar(master, value="None")
        self.currentval = Label(master, textvar=self.currentvalstringvar)
        self.currentval.grid(row=2, column=5)

        self.packageindicator = StringVar(master, value="!")
        self.packageindicatorlabel = Label(master, textvar=self.packageindicator, font=("times", 20, "bold"))
        self.packageindicatorlabel.grid(row=4, column=5)
        self.packageindicator.set(".")
        self.datasource.packageindicator = packageindicator

        # OptionMenu lists
        _npoints_list = [10, 25, 50, 75, 100, 250, 500, 750, 1000]  # Desired points
        npoints_list = [str(x) for x in _npoints_list]  # Converting each of these to a string
        available_ports = self.datasource.findAllSerialPorts()

        if len(available_ports) == 0:  # If there are no available ports, print a warning
            logger.warning("No available ports!")
            available_ports.append("None")

        _baud_rates = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000]
        baud_rates = [str(x) for x in _baud_rates]
        input_num_options = [str(x) for x in range(1, args.max_inputs + 1)]

        plotmethods = ["Markers only", "Line only", "Both"]  # Various ways to display the plotted values

        # StringVars
        self.npointsentrystr = StringVar(master, value="250")
        self.baudrateentrystr = StringVar(master, value="115200")
        self.portentrystr = StringVar(master, value=available_ports[-1])
        self.plotmethodentrystr = StringVar(master, value=plotmethods[1])
        self.numinputsentrystr = StringVar(master, value="1")

        # Using OptionMenu instead:
        self.plotmethodoptionmenu = OptionMenu(master, self.plotmethodentrystr, *plotmethods)
        self.plotmethodoptionmenu.grid(row=4, column=2)

        self.npointsoptionmenu = OptionMenu(master, self.npointsentrystr, *npoints_list)
        self.npointsoptionmenu.grid(row=1, column=1, sticky="W")

        self.baudrateoptionmenu = OptionMenu(master, self.baudrateentrystr, *baud_rates)
        self.baudrateoptionmenu.grid(row=2, column=1, sticky="W")

        self.portoptionmenu = OptionMenu(master, self.portentrystr, *available_ports)
        self.portoptionmenu.width = 20
        self.portoptionmenu.grid(row=3, column=1, sticky="W")

        self.numinputsoptionmenu = OptionMenu(master, self.numinputsentrystr, *input_num_options)
        self.numinputsoptionmenu.grid(row=4, column=1, sticky="W")

        # Buttons
        self.show_x_axis = IntVar(master, value=0)
        self.showxaxischeckbutton = Checkbutton(master, text="Show y=0", variable=self.show_x_axis, onvalue=1, offvalue=0)
        self.showxaxischeckbutton.grid(row=1, column=2)

        self.connectbutton = Button(master, text="Connect", command=self.datasource.connectToSerial)
        self.connectbutton.grid(row=2, column=3)

        self.disconnectbutton = Button(master, text="Disconnect", command=self.datasource.disconnectFromSerial)
        self.disconnectbutton.grid(row=3, column=3)

        self.refreshserialbutton = Button(master, text="Refresh Ports", command=self.datasource.refreshSerial)
        self.refreshserialbutton.grid(row=3, column=2)

        self.exportdatabutton = Button(master, text="Export", command=self.datasource.exportData)
        self.exportdatabutton.grid(row=4, column=3)

        self.printrawdata = IntVar(master, value=0)
        self.printrawbutton = Checkbutton(
            master, text="Print raw data", variable=self.datasource.printRawData, onvalue=1, offvalue=0
        )
        self.printrawbutton.grid(row=2, column=2)

        self.requirebrackets = IntVar(master, value=1)
        self.requirebracketsbutton = Checkbutton(
            master, text="Require brackets", variable=self.requirebrackets, onvalue=1, offvalue=0
        )
        self.requirebracketsbutton.grid(row=3, column=5)

    # =========================================================================
    # Runs the main loop for Tk().
    def mainloop(self):
        # Schedule the first execution of plotter
        self.master.after(TIMEDELAY, self.plotline)
        self.master.mainloop()
        return

    # =====================================================================
    def die(self):
        logger.debug("Window closed")
        sys.exit()

    # =========================================================================
    # Plots the data to the GUI's plot window.
    def plotline(self):
        numpoints = int(self.npointsentrystr.get())
        numinputs = int(self.numinputsentrystr.get())

        if self.plotmethodentrystr.get() == "Markers only":
            plotmethod = "."
        elif self.plotmethodentrystr.get() == "Line only":
            plotmethod = "-"
        else:
            plotmethod = ".-"
        self.a1.clear()

        for i in range(numinputs):  # Plot each line individually
            plotline = [x[i] for x in self.datasource.serial_plotline]
            self.a1.plot(plotline, plotmethod, label=str(i))

        self.a1.grid()
        if self.show_x_axis.get():
            self.a1.set_ylim(0, 1.125 * np.amax(np.array(self.serial_data)))

        # Plot formatting parameters
        ticklabels = np.linspace(numpoints / 10, 0, 5)
        self.a1.set(xticks=np.linspace(0, numpoints, 5), xticklabels=ticklabels)
        self.a1.set_xticklabels([])
        self.a1.set_ylabel("Serial Value")
        self.a1.legend(loc=3)
        self.a1.set_title("Serial Values")

        self.canvas1.draw()  # Actually update the GUI's canvas object
        # Schedule the next execution of plotter
        self.master.after(TIMEDELAY, self.plotline)
        return

    # =========================================================================
    # Swap out the string label indicating whether serial is connected.
    def toggleSerialConnectedLabel(self, connection):
        if connection:
            self.serialconnectedstringvar.set("Connected")
            self.serialconnectedlabel.config(fg="green")
        else:
            self.serialconnectedstringvar.set("Unconnected")
            self.serialconnectedlabel.config(fg="red")
        return
