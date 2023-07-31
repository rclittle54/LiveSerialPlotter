#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 11:42:26 2019

Live Serial Plotter

@author: ryanlittle
"""
import argparse
import logging
import sys
import tkinter

from LiveDataSource import LiveDataSource
from PlotterWindow import PlotterWindow

logger = logging.getLogger(__name__)


# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="loranet bridge")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity of outut")
    parser.add_argument("--max-points", default=10000, help="Maximum number of points to store (default: %(default)s)")
    parser.add_argument("--max-inputs", default=5, help="Maximum number of vars to plot (default: %(default)s)")
    args = parser.parse_args()

    if args.verbose == 0:
        level = logging.WARNING
    elif args.verbose == 1:
        level = logging.INFO
    elif args.verbose > 1:
        level = logging.DEBUG

    logging.basicConfig(format="%(asctime)s.%(msecs)03d: %(message)s", level=level, stream=sys.stdout, datefmt="%H:%M:%S")

    logger.debug("Running.")

    pw = PlotterWindow(args)
    LiveDataSource(args, pw)
    pw.mainloop()

    logger.debug("Quitting.")


if __name__ == "__main__":
    main()
