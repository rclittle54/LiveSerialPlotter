#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Tk code to plot live data
"""

from argparse import Namespace
import datetime
import logging
import matplotlib

matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sys
from tkinter import Tk, Label, StringVar, Button, OptionMenu, IntVar, Checkbutton

from LiveDataSource import LiveDataSource

logger = logging.getLogger(__name__)

TIMEDELAY = 100  # Milliseconds between updating plot
PLOTRATIO = (9, 6)
PLOTDPI = 100


# =============================================================================
# Main GUI window class.
class PlotterWindow:
    def __init__(self, args: Namespace):
        master = Tk()
        self.master = master
        self.master.title("Live Serial Plotter")
        self.master.resizable(False, False)  # Prevent resizing

        # The data, kept up-to-date by the LiveDataSource
        self.queue = None
        self.data = []
        self.labels = []

        # set up a close window handler
        master.protocol("WM_DELETE_WINDOW", self.die)

        # Figure
        self.f1 = plt.figure(figsize=PLOTRATIO, dpi=PLOTDPI)
        self.a1 = self.f1.add_subplot(111)
        self.a1.grid()
        self.a1.set_title("Data Values")
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
        self.serialconnectedlabel = Label(
            master, textvar=self.serialconnectedstringvar, fg="red", width=15
        )
        self.serialconnectedlabel.grid(row=1, column=3)

        self.numinputslabel = Label(master, text="# Inputs")
        self.numinputslabel.grid(row=4, column=0, sticky="W")

        self.currentvallabel = Label(master, text="Most recent:")
        self.currentvallabel.grid(row=1, column=5)

        self.currentvalstringvar = StringVar(master, value="None")
        self.currentval = Label(master, textvar=self.currentvalstringvar)
        self.currentval.grid(row=2, column=5)

        self.packageindicator = StringVar(master, value="!")
        self.packageindicatorlabel = Label(
            master, textvar=self.packageindicator, font=("times", 20, "bold")
        )
        self.packageindicatorlabel.grid(row=4, column=5)
        self.packageindicator.set(".")

        npoints_list = [str(x) for x in [10, 25, 50, 75, 100, 250, 500, 750, 1000]]
        available_ports = ["unk"]
        baud_rates = ["unk"]
        input_num_options = [str(x) for x in range(1, args.max_inputs + 1)]
        plotmethods = [
            "Markers only",
            "Line only",
            "Both",
        ]  # Various ways to display the plotted values

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
        self.showxaxischeckbutton = Checkbutton(
            master, text="Show y=0", variable=self.show_x_axis, onvalue=1, offvalue=0
        )
        self.showxaxischeckbutton.grid(row=1, column=2)

        self.connectbutton = Button(master, text="Connect", command=None)
        self.connectbutton.grid(row=2, column=3)

        self.disconnectbutton = Button(master, text="Disconnect", command=None)
        self.disconnectbutton.grid(row=3, column=3)

        self.refreshserialbutton = Button(master, text="Refresh Ports", command=None)
        self.refreshserialbutton.grid(row=3, column=2)

        self.exportdatabutton = Button(master, text="Export", command=self.exportData)
        self.exportdatabutton.grid(row=4, column=3)

        self.printrawdata = IntVar(master, value=0)
        self.printrawbutton = Checkbutton(
            master, text="Print raw data", variable=self.printrawdata, onvalue=1, offvalue=0
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
        self.master.quit()
        return

    # =========================================================================
    # Exports the data to a file associated with the current date and time.
    def exportData(self):
        timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        outfname = "SessionLogs/SerialSessionLog_%s.csv" % (timestamp)
        try:
            hit_data_start = False
            f = open(outfname, "w")
            for sd in self.serial_data:
                # Check if we have data yet, don't start appending until that point
                if not hit_data_start:
                    if not any(sd):
                        continue  # Skip to the next data point if all values are zeros
                    else:
                        hit_data_start = True

                wstr = ""
                for d in sd:
                    wstr += "%f," % (d)
                wstr = wstr[:-1] + "\n"
                f.write(wstr)
            f.close()
            logger.info("Successfully exported to %s" % (outfname))
        except:
            logger.warning("Error: Unable to export data")
        return

    # =========================================================================
    # Plots the data to the GUI's plot window.
    def plotline(self):
        numpoints = int(self.npointsentrystr.get())

        if self.plotmethodentrystr.get() == "Markers only":
            plotmethod = "."
        elif self.plotmethodentrystr.get() == "Line only":
            plotmethod = "-"
        else:
            plotmethod = ".-"
        self.a1.clear()

        d = np.array(self.data[-numpoints:])
        self.a1.plot(d, plotmethod, label=self.labels)

        self.a1.grid()
        if self.show_x_axis.get():
            self.a1.set_ylim(0, 1.125 * np.amax(d))

        # Plot formatting parameters
        ticklabels = np.linspace(numpoints / 10, 0, 5)
        self.a1.set(xticks=np.linspace(0, numpoints, 5), xticklabels=ticklabels)
        self.a1.set_xticklabels([])
        self.a1.set_ylabel("Serial Value")
        self.a1.legend(loc=3)

        self.canvas1.draw()  # Actually update the GUI's canvas object
        # Schedule the next execution of plotter
        self.master.after(TIMEDELAY, self.plotline)
