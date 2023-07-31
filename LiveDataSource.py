# -*- coding: utf-8 -*-
"""
This class takes care of getting up-to-date data. It spawns off a thread to keep
some np arrays up-to-date and also provides some tk callbacks to configure it.

It accepts data from either a serial port or from a udp socket.
"""
from argparse import Namespace
import datetime
import glob
import logging
import numpy as np
import serial
import sys

logger = logging.getLogger(__name__)

TIMEDELAY = 100  # Milliseconds between getting new data


class LiveDataSource:
    def __init__(self, args: Namespace, window):
        self.ser = None
        self.master = window.master
        self.window = window
        self.IS_SERIAL_CONNECTED = False
        self.printRawData = False

        self.refreshSerial()
        menu = self.window.baudrateoptionmenu["menu"]
        menu.delete(0, "end")
        baud_rates = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000]
        for v in baud_rates:
            menu.add_command(label=str(v), command=lambda value=str(v): self.om_variable.set(value))

        self.window.connectbutton["command"] = self.connectToSerial
        self.window.disconnectbutton["command"] = self.disconnectFromSerial
        self.window.refreshserialbutton["command"] = self.refreshSerial
        self.window.exportdatabutton["command"] = self.exportData

    # =============================================================================
    # This function comes graciously from StackOverflow
    # Finds all available serial ports, and returns as a list.
    def findAllSerialPorts(self):
        if sys.platform.startswith("win"):
            ports = ["COM%s" % (i + 1) for i in range(256)]
        elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob("/dev/tty[A-Za-z]*")
        elif sys.platform.startswith("darwin"):
            # This only works on "newer" OSX releases
            ports = glob.glob("/dev/cu.usb*")
        else:
            raise EnvironmentError("Unsupported platform")
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except:
                logger.warning(f"Error opening {port}")
        return result

    # =============================================================================
    # Closes all serial ports.
    def closeAllSerialPorts(self):
        ports = self.findAllSerialPorts()
        for p in ports:
            try:
                p.close()
            except:
                continue
        self.IS_SERIAL_CONNECTED = False

    # =========================================================================
    # Connects GUI to a COM port based on the user selected port.
    def connectToSerial(self):
        try:
            port = self.window.portentrystr.get()
            baudrate = int(self.window.baudrateentrystr.get())
            logger.debug("Connecting to %s at %d" % (port, baudrate))
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
            self.ser.flushInput()
        except:
            logger.warn(f"Could not connect to {port}")
            self.toggleSerialConnectedLabel(False)
            return -1

        self.IS_SERIAL_CONNECTED = True  # Set GUI state
        self.toggleSerialConnectedLabel(True)  # Show the state
        self.getSerialValue()
        logger.debug("Connected")

    # =========================================================================
    # Disconnects from whatever serial port is currently active.
    def disconnectFromSerial(self):
        if self.IS_SERIAL_CONNECTED:  # Only do this if already connected.
            self.ser.close()
            self.toggleSerialConnectedLabel(False)
            self.IS_SERIAL_CONNECTED = False

    # =========================================================================
    # Swap out the string label indicating whether serial is connected.
    def toggleSerialConnectedLabel(self, connection):
        if connection:
            self.window.serialconnectedstringvar.set("Connected")
            self.window.serialconnectedlabel.config(fg="green")
        else:
            self.window.serialconnectedstringvar.set("Unconnected")
            self.window.serialconnectedlabel.config(fg="red")

    # =========================================================================
    # Refreshes the list of available serial ports on the option menu.
    def refreshSerial(self):
        new_serial_list = self.findAllSerialPorts()

        logger.info("Refreshing serial port list")
        if len(new_serial_list) == 0:
            logger.warn("No available serial ports.")
            return

        self.window.portentrystr.set(new_serial_list[-1])  # Set the variable to none
        self.window.portoptionmenu["menu"].delete(0, "end")  # Delete the old list

        for port in new_serial_list:
            logger.debug(f"Adding {port}")
            self.window.portoptionmenu["menu"].add_command(label=port, command=lambda v=port: self.om_variable.set(v))

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
    # Changes the "good data received" indicator.
    def setPackageIndicator(self, state):
        if state == "good":
            self.window.packageindicator.set("!")
            self.window.packageindicatorlabel.config(fg="green", font=("times", 20, "bold"))
        else:
            self.window.packageindicator.set(".")
            self.window.packageindicatorlabel.config(fg="black", font=("times", 20, "bold"))

    # =========================================================================
    # Gets the most recent serial value from connection. IMPORTANT.
    def getSerialValue(self):
        if not self.IS_SERIAL_CONNECTED:
            logger.warning("No serial connection")
            return

        # Schedule the next execution of this function
        self.master.after(TIMEDELAY, self.getSerialValue)

        rawdata = self.ser.readline().decode("utf8").strip()
        if len(rawdata) == 0:
            return
        if self.window.printrawdata.get():
            logger.info(rawdata)
        l = rawdata.rfind(">")
        if l == -1:
            logger.warning("No > delimiter")
            self.setPackageIndicator("bad")
            return
        if self.window.requirebrackets.get():
            r = rawdata.find("<")
            if r == -1:
                logger.warning("No < delimiter")
                self.setPackageIndicator("bad")
                return
        else:
            r = len(rawdata[l + 1 :])
        splits = rawdata[l + 1 : r].split(" ")
        logger.debug(f"splits:{splits}")
        try:
            splits = [float(v) for v in splits]
        except ValueError:
            logger.warning(f"Failed to convert {splits}")
            self.setPackageIndicator("bad")
            return

        self.setPackageIndicator("good")

        self.window.data.append(splits)
