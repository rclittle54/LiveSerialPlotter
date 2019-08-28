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
automatic scaling.