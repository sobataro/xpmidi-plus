Xpmidi+
======

An improved version of Xpmidi, a tkinter frontend for pmidi or aplaymidi.



System Requirements
------

You need following programs:

* MIDI player e.g. `aplaymidi` or `pmidi`
* Python 3 or greater
* tcl/tk and tkinter



Usage
------

Just execute `xpmidiplus.py` script. No instllation is needed.

To be written in more detailed



Command Line Options
------

This chapter was just copied from original xpmidi's README. 
To be revised

xpmidi recognizes the following on the command line:

 -v   Prints the version number and exits

 DIRNAME - you can pass a single directory name on the command line. This is scanned
           of midi file (actually, any names ending in '.mid'). The filenames are
           displayed in the selector. Only 1 directory name can be used.

 FILES   - you can supply one or more midi filenames instead of a directory.

You can't mix FILES and DIRNAME on the command line.



Settings File (~/.xpmidirc)
------

This chapter was just copied from original xpmidi's README. 
To be revised
	
Xpmidi stores the name of the last used directory and the list of favorite
directories in the RC file `~/.xpmidirc`. This is an invisible file in
the user's home directory.



Options
------

To be written



Bugs and Issues
------

* User interface is not good
    * Original xpmidi works well, but I was dissatisfied with the original UI... That was why I developing xpmidi+
    * Current xpmidi+ is mush the same as original.



Contacts
------

Xpmidi+ is written by tuxjunky <tuxjunky@gmail.com>.

Original xpmidi is written by Bob van der Poel <bob@mellowood.ca>.
Original program can be obtained from http://www.mellowood.ca.



Copyright and License
------

Xpmidi+ is copyright tuxjunky, 2013.
The original program xpmidi is copyright Robert van der Poel, 2003-2009.

The original xpmidi is distributed under GPLv2, and xpmidi+ follows it.
(See the COPYING file)
