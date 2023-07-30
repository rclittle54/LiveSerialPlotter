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
import serial
import sys
from tkinter import Tk

logger = logging.getLogger(__name__)

TIMEDELAY = 100  # Milliseconds between getting new data/updating plot

class LiveDataSource:
    def __init__(self, master: Tk, args: Namespace):
        self.ser = None
        self.master = master
        self.IS_SERIAL_CONNECTED = False
        self.data = [[0 for i in range(args.max_inputs)] for i in range(args.max_points)]
        self.serial_plotline = []
        self.ports = []
        self.printRawData = False

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
        return

    # =========================================================================
    # Connects GUI to a COM port based on the user selected port.
    def connectToSerial(self):
        try:
            port = self.portentrystr.get()
            baudrate = int(self.baudrateentrystr.get())
            logger.debug("Connecting to %s at %d" % (port, baudrate))
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
            self.ser.flushInput()
        except:
            logger.warn("Error")
            self.ToggleSerialConnectedLabel(False)
            return -1

        self.IS_SERIAL_CONNECTED = True  # Set GUI state
        self.ToggleSerialConnectedLabel(True)  # Show the state
        self.GetSerialValue()  # Begin the GetSerialValue() loop
        logger.debug("Connected")
        return

    # =========================================================================
    # Disconnects from whatever serial port is currently active.
    def disconnectFromSerial(self):
        if self.IS_SERIAL_CONNECTED:  # Only do this if already connected.
            self.ser.close()
            self.ToggleSerialConnectedLabel(False)
            self.IS_SERIAL_CONNECTED = False
        return

    # =========================================================================
    # Refreshes the list of available serial ports on the option menu.
    def refreshSerial(self):
        new_serial_list = findAllSerialPorts()

        logger.info("Refreshing serial port list")
        if len(new_serial_list) == 0:
            logger.warn("No available serial ports.")
            return

        self.portentrystr.set(new_serial_list[-1])  # Set the variable to none
        self.portoptionmenu["menu"].delete(0, "end")  # Delete the old list

        for port in new_serial_list:  # Refresh:
            self.portoptionmenu["menu"].add_command(label=port, command=_setit(self.portentrystr, port))
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
    # Changes the "good data received" indicator.
    def setPackageIndicator(self, state):
        if state == "good":
            self.packageindicator.set("!")
            self.packageindicatorlabel.config(fg="green", font=("times", 20, "bold"))
        else:
            self.packageindicator.set(".")
            self.packageindicatorlabel.config(fg="black", font=("times", 20, "bold"))
        return

    # =========================================================================
    # Gets the most recent serial value from connection. IMPORTANT.
    def getSerialValue(self):
        if not self.IS_SERIAL_CONNECTED:
            logger.warning("No serial connection")
            return

        # Schedule the next execution of this function
        self.master.after(TIMEDELAY, self.GetSerialValue)

        rawdata = self.ser.readline().decode("utf8").strip()
        if len(rawdata) > 0:
            try:
                self.currentvalstringvar.set(str(rawdata))
                if self.printRawData.get():
                    logger.info(rawdata)

                if self.requirebrackets.get():
                    if ">" in rawdata and "<" in rawdata:
                        x = rawdata[1:-2]
                        try:
                            npoints = int(self.npointsentrystr.get())
                            x_split = x.split(" ")
                            # Make sure that every data package is the same length, so it's not a sequence
                            senddata = []
                            for i in range(MAXINPUTS):
                                try:
                                    senddata.append(float(x_split[i]))
                                except:
                                    senddata.append(self.data[-1][i])  # Append the most recent value

                            self.data.append(senddata)
                            self.data = self.data[1:]
                            self.serial_plotline = self.data[-npoints:]

                            # Set the blinker indicator to green!
                            self.SetPackageIndicator("good")

                            self.master.after_idle(self.Plotline)  # Once everything's done, plot it!
                        except ValueError:
                            logger.warning("Invalid serial value: Non-floating point detected: %s" % (x))

                    else:
                        self.SetPackageIndicator("bad")
                else:
                    x = rawdata
                    try:
                        npoints = int(self.npointsentrystr.get())
                        x_split = x.split(" ")
                        # Make sure that every data package is the same length, so it's not a sequence
                        senddata = []
                        for i in range(self.args.max_inputs):
                            try:
                                senddata.append(float(x_split[i]))
                            except:
                                senddata.append(self.data[-1][i])  # Append the most recent value

                        self.data.append(senddata)
                        self.data = self.data[1:]
                        self.serial_plotline = self.data[-npoints:]
                        self.master.after_idle(self.Plotline)
                    except ValueError:
                        logger.warning("Invalid serial value: Non-floating point detected: %s" % (x))

            except Exception as e:
                logger.warning("Error in GetSerialValue()", e)
