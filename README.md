Xpmidi+
======

An improved version of Xpmidi, a tkinter frontend for pmidi or aplaymidi.



Functions
------

### Original xpmidi's functions
* MIDI playback via `aplaymidi` or `pmidi`
* Playlists / Favorite directories function
* PDF display
    * Xpmidi can display music score without any operations (You must prepare the .pdf file of the score)

### Xpmidi+'s additional functions / features
* Send _System Exclusive_ message before each playback to reset tone generator
    * Preset: GM System ON, GS Reset, XG System ON
    * If you want to use other System Exclusive or some reset messages, you can set any MIDI file to sent
* Continuous playback (whole files of directory / playlist)
    * Original xpmidi doesn't have this...
* Bug fixes
* UI enhancement



System Requirements
------

Xpmidi+ needs following programs:

* MIDI player e.g. `aplaymidi` or `pmidi`
* Python 3 or greater
* tcl/tk and tkinter



Usage
------

Just execute `xpmidiplus.py` script. No instllation is needed.

To be written in more detailed



Options
------

To be written



Command Line Options
------

(This chapter was just copied from original xpmidi's README. To be revised)

xpmidi recognizes the following on the command line:

 -v   Prints the version number and exits

 DIRNAME - you can pass a single directory name on the command line. This is scanned
           of midi file (actually, any names ending in '.mid'). The filenames are
           displayed in the selector. Only 1 directory name can be used.

 FILES   - you can supply one or more midi filenames instead of a directory.

You can't mix FILES and DIRNAME on the command line.



Settings File (~/.xpmidirc)
------

Xpmidi+ stores settings in the RC file `~/.xpmidiplusrc`.

When xpmidi+ started, this file is excuted as Python source code.



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
