==================================================
Live Serial Plotter
- Author: Ryan Little,
	  Locomotor Control Systems Lab, UT Dallas
	  2019	
==================================================

This program utilizes Python and Tkinter to show the 
user a GUI with customizable options for displaying 
and plotting serial input. There can be single or
multiple floating point values sent, space delimited.
An example is as follows:

>##.## ##.## ##.##<\n

Having the brackets present allows verification of
full package receipt, which can prevent annoying
sudden drops to zero of the data, ruining Matplotlib's
automatic scaling. However, the brackets are not strictly
needed, as long as the "Require brackets" option is
unchecked.

The following options are available for customization:
* # Points
	- Determines the number of data points to plot
	  in the plot window.
* Baud Rate
	- Determines what baud rate to establish the
	  serial connection.
* Serial Port
	- List of available serial ports.
* # Inputs
	- Determines how many space delimited inputs to
	  look for and plot.
* Show y=0
	- Forces the plot window to show the x-axis, 
	  preventing auto-scaling on the lower side.
* Print raw data
	- Prints the raw data received to the console.
* Refresh ports
	- Refreshes the list of COM ports available.
* Line style
	- Allows for plotting either line only, markers
	  only, or both.
* Require brackets
	- Allows the user to specify if the data to look
	  for will have package delimiting brackets or
	  not.  