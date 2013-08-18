#!/usr/bin/env python3

"""
Copyright (C) 2013  tuxjunky

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; Version 2 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from tkinter import *
import tkinter.filedialog
import tkinter.messagebox
import os, sys, signal, glob, time, getopt, shlex
from array import array
from struct import pack
from player import Player


# UGLY GLOBAL VARIABLES...

player = Player()

rc_file = os.path.expanduser("~/.xpmidiplusrc")
version = 0.2

fullsize = 0          # command line option for fullscreen

## These are stored in the rc_file on exit. Some can
## be modified via the options menu.

current_dir = ['.']
favorite_dirs = []
player_program = "aplaymidi"
player_options = "-p 20:0"      # Player options
sysex = "GM"
background_color = "white"          # listbox colors
foreground_color = "medium blue"
displayProgram = ""
displayOptions = ""
displayDir = []

#############################################################

def usage():
    """ Display usage message and exit. """

    print("Xpmidi+, GUI frontend for MIDI Player")
    print("(c) 2012, tuxjunky")
    print("Usage: xpmidiplus.py [opts] [dir | Midifiles]")
    print("Options:")
    print("   -f    start full size")
    print("   -v    display version number")
    sys.exit(0)


####################################################################
## These functions create various frames. Maintains consistency
## between different windows (and makes cleaner code??).

def makeMenu(parent, buttons=(())):
    m = Menu(parent)
    parent.configure(menu = m)
    for txt, cmd in buttons:
        m.add_command(label=txt, command=cmd)

    return m

def makeLabelBox(parent, justify=CENTER, row=0, column=0, text=''):
    """ Create a label box. """

    f = Frame(parent)
    b = Label(f,justify=justify, text=text)
    b.grid()
    f.grid(row=row, column=column, sticky=E+W)
    f.grid_rowconfigure(0, weight=1)

    return b

def makeListBox(parent, width=50, height=20, selectmode=BROWSE, row=0, column=0):
    """ Create a list box with x and y scrollbars. """

    f = Frame(parent)
    ys = Scrollbar(f)
    xs = Scrollbar(f)
    listbox = Listbox(f,
        bg=background_color,
        fg=foreground_color,
        width=width,
        height=height,
        yscrollcommand=ys.set,
        xscrollcommand=xs.set,
        exportselection=FALSE,
        selectmode=selectmode)

    ys.config(orient=VERTICAL, command=listbox.yview)
    ys.grid(column=0,row=0, sticky=N+S)

    xs.config(orient=HORIZONTAL, command=listbox.xview)
    xs.grid(column=1, row=1, sticky=E+W)

    listbox.grid(column=1,row=0, sticky=N+E+W+S)

    f.grid(row=row, column=column, sticky=E+W+N+S)
    f.grid_rowconfigure(0, weight=1)
    f.grid_columnconfigure(1, weight=1)
    return listbox

def makeEntry(parent, label="Label", text='', column=0, row=0):

    f=Frame(parent)
    l=Label(f, anchor=E, width=15, padx=20, pady=10, text=label).grid(column=0, row=0)
    e=Entry(f, text=text, width=30)
    e.grid(column=1, row=0, sticky=E)
    e.delete(0, END)
    e.insert(END, text)
    f.grid( column=column, row=row)

    return e

#########################################
# We have 3 class, 1 for each window we create.


########################################
# Options dialog

class setOptions(object):

    def __init__(self):
        self.f=f=Toplevel()
        if root.winfo_viewable():
            f.transient(root)

        makeMenu(f, buttons=(
            ("Cancel", self.f.destroy), ("Apply", self.apply)))
        self.playerEnt =  makeEntry(f, label="MIDI Player",      text=player_program,   row=1)
        self.playOptEnt = makeEntry(f, label="Player Options",   text=player_options, row=2)
        self.sysexEnt =   makeEntry(f, label="SysEX",            text=sysex,    row=3)
        self.fgEnt =      makeEntry(f, label="Foreground Color", text=foreground_color,   row=4)
        self.bgEnt =      makeEntry(f, label="Background Color", text=background_color,   row=5)

        self.displayPrg = makeEntry(f, label="PDF Display", text=displayProgram, row=6)
        self.displayOpt = makeEntry(f, label="PDF Options", text=displayOptions, row=7)
        self.displayPath = makeEntry(f, label="PDF Path", text=', '.join(displayDir), row=9)

        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)

        f.grab_set()
        root.wait_window(f)


    def apply(self):
        global player_program, player_options, sysex
        global foreground_color, background_color
        global displayProgram, displayOptions, displayDir

        player_program = self.playerEnt.get()
        player_options = self.playOptEnt.get()
        sysex = self.sysexEnt.get()

        displayProgram = self.displayPrg.get()
        displayOptions = self.displayOpt.get()
        fg = self.fgEnt.get()
        bg = self.bgEnt.get()

        try:
            app.listbox.config(fg=fg)
            foreground_color = fg
        except TclError:
            tkinter.messagebox.showerror("Set Forground Color",
                "Illegal foreground color value")

        try:
            app.listbox.config(bg=bg)
            background_color = bg
        except TclError:
            tkinter.messagebox.showerror("Set Background Color",
                "Illegal background color value")

        self.f.destroy()


########################################
# A listbox with the favorites directory

class selectFav(object):

    def __init__(self):
        self.f=f=Toplevel()
        if root.winfo_viewable():
            f.transient(root)

        makeMenu(f, buttons=(
            ("Open", self.select),
            ("Add Current", self.addToFav),
            ("Delete", self.delete)))

        self.listbox = makeListBox(f, height=10, selectmode=MULTIPLE, row=2, column=0)
        self.listbox.bind("<Double-Button-1>", self.dclick)

        # Make the listbox frame expandable

        f.grid_rowconfigure(2, weight=1)
        f.grid_columnconfigure(0, weight=1)

        self.updateBox()

        f.grab_set()
        f.focus_set()
        f.wait_window(f)


    def dclick(self, w):
        """ Callback for doubleclick. Just do one dir. """

        self.doSelect( [self.listbox.get(self.listbox.nearest(w.y))] )


    def select(self):
        """ Callback for the 'select' button. """

        l=[]
        for n in self.listbox.curselection():
            l.append(self.listbox.get(int(n)))
        self.doSelect(l)


    def doSelect(self, n):
        """ Update the filelist. Called from select button or doubleclick."""

        global current_dir

        if n:
            current_dir = n
            app.updateList()
        self.f.destroy()


    def addToFav(self):
        """ Add the current directory (what's displayed) to favorites."""

        for n in current_dir:
            if n and not favorite_dirs.count(n):
                favorite_dirs.append(n)

        favorite_dirs.sort()
        self.updateBox()

    def delete(self):
        """ Delete highlighted items, Called from 'delete' button. """

        global favorite_dirs

        l=[]
        for n in self.listbox.curselection():
            l.append(self.listbox.get(int(n)))

        if l:
            if tkinter.messagebox.askyesno("Delete Directory",
                     "Are you sure you want to delete the "
                     "highlighted directories from the favorites list?",
                      parent=self.f):

                for n in l:
                    favorite_dirs.remove(n)

                self.updateBox()


    def updateBox(self):
        global favorite_dirs

        self.listbox.delete(0, END)
        for n in favorite_dirs:
            self.listbox.insert(END, n)


############################
# Main display screen

class Application(object):

    def __init__(self):
        """ Create 3 frames:
               bf - the menu bar
               lf - the list box with a scroll bar
               mf - a label at the bottom with the current filename.
        """

        self.menu = makeMenu(root, buttons=(
             ("Stop", self.stopPmidi),
             ("Open Dir", self.chd),
             ("Load Playlist", self.playList),
             ("Favorites", selectFav),
             ("Options", setOptions)))

        self.msgbox = makeLabelBox(root, justify=LEFT, row=2, column=0)

        self.listbox = makeListBox(root, height=28, row=1, column=0)

        self.elasped = 0

        # Make the listbox frame expandable

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # some bindings

        self.listbox.bind("<Return>", self.loadfileRet)
        self.listbox.bind("<Double-1>", self.loadfileDoubleClick)

        self.listbox.bind('<Button-3>', self.stopPmidi)
        root.bind('<Escape>', self.stopPmidi)

        root.protocol("WM_DELETE_WINDOW", self.quitall)

        for a in 'abcdefghijklmnopqrstuvwxyz':
            root.bind(a, self.keyPress)

        self.listbox.bind('<F1>', self.displayOnly)
        self.listbox.bind('<F2>', self.rotateDisplayList)

        # end bindings

        self.listbox.focus_force()   # make the listbox use keyboard

        self.CurrentFile = None
        self.next_file_index = None
        self.fileList = {} # dict of files in listbox. Key is displayed name, data=actual

        self.updateList()
        self.welcome()
        player.play_sysex(sysex, player_program, player_options, os.P_NOWAIT)


    def welcome(self):
        # Display message in status box
        if current_dir:
            c = ', '.join(current_dir)
        else:
            c = ' '
        if not player.is_playing():
            self.msgbox.config(text="XPmidi+\n%s" % c)

    lastkey = ''
    lastkeytime = 0

    def keyPress(self, ev):
        """ Callback for the alpha keys a..z. Finds 1st entry matching keypress. """

        c = self.lastKeyHit = ev.char.upper()

        # Timer. If there is less than 3/4 second between this key and
        # the previous we concat the keypress string. Else, start with
        # new key.

        tm = time.time()
        delay = tm - self.lastkeytime
        self.lastkeytime = tm     # save time of this key for next time

        if delay < .75:
            self.lastkey += c
        else:
            self.lastkey = c

        # the search target and size
        c = self.lastkey
        sz = len(c)

        for x,a in enumerate(self.listbox.get(0, END)):
            if a[0:sz].upper() >= c:
                self.listbox.select_clear(ACTIVE) # needed to un-hilite existing selection
                self.listbox.activate(x)
                self.listbox.see(x)
                self.listbox.select_set(x)
                break



    """ Play a selected file. This is a listbox callback.
        Two callback funcs are needed: one for a mouse click,
        the other for a <Return>.
    """

    def loadfileRet(self, w):
        """ Callback for <Return>. """

        self.loadfile(self.listbox.get(ACTIVE))

    def loadfileDoubleClick(self, w):
        """ Callback for <Double-1>. """

        self.listbox.activate(self.listbox.nearest(w.y))
        self.loadfile(self.listbox.get(self.listbox.nearest(w.y)))


    def loadfile(self, file_name):
        if not file_name:
            return

        print(file_name)
        self.CurrentFile = file_name
        file_path = self.fileList[file_name]
        player.stop()

        # set the index of next file
        list_size = self.listbox.size()
        file_name_list = self.listbox.get(0, list_size)
        self.next_file_index = (file_name_list.index(self.CurrentFile) + 1) % list_size

        player.view(file_path, displayDir, displayProgram, displayOptions)
        player.play(file_path, player_program, player_options,
                    os.P_NOWAIT, root, self.update_statusbar, self.play_next)

        root.update()


    def stopPmidi(self):
        """ Stop currently playing MIDI. """

        player.stop()

        self.msgbox.config(text="Stopping...%s\n" % self.CurrentFile)
        root.update_idletasks()

        player.play_sysex(sysex, player_program, player_options, os.P_WAIT)
        self.welcome()
        time.sleep(.5)


    def update_statusbar(self, time):
        self.msgbox.config(text="[%02d:%02d]: %s\n%s" %
            (int(time / 60), int(time % 60), self.CurrentFile, current_dir[0]))


    def play_next(self):
        self.welcome()
        if self.next_file_index is not None:
            list_size = self.listbox.size()
            self.listbox.selection_clear(0, list_size)
            self.listbox.selection_set(self.next_file_index)
            self.listbox.activate(self.next_file_index)
            self.listbox.see(self.next_file_index)
            self.loadfile(self.listbox.get(0, list_size)[self.next_file_index])



    # PDF display

    def rotateDisplayList(self, w):
        """ Callback for <F2>. Rotate display PDF list"""

        global displayDir
        if not len(displayDir):
            return

        displayDir.append(displayDir.pop(0))
        opts={'aspect':4}
        tkinter.messagebox.showinfo(message="DisplayPDF dir: %s" % displayDir[0])

    def displayOnly(self, w):
        """ Callback for <F1>. """

        player.stop()
        player.view(self.fileList[self.listbox.get(ACTIVE)], displayDir,
                    displayProgram, displayOptions)


    def chd(self):
        """ Callback from <Open Dir> button.
            Switch to new directory and updates list.
        """

        global current_dir

        new_directory = tkinter.filedialog.askdirectory(initialdir=','.join(current_dir))

        if new_directory:
            current_dir = [new_directory]
            self.updateList()



    def quitall(self, ex=''):
        """ All done. Save current dir, stop playing and exit. """

        self.stopPmidi()

        def writeoption(s):
            print("%s = %s" % (s, eval(s)))

        # The options by name and a 'type': 'list', 'string', 'integer'
        options = [
            ['favorite_dirs', 'l'],
            ['current_dir', 'l'],
            ['background_color', 's'],
            ['foreground_color', 's'],
            ['player_options', 's'],
            ['player_program', 's'],
            ['sysex', 's'],
            ['displayProgram', 's'],
            ['displayOptions', 's'],
            ['displayDir', 'l']  ]

        f=open(rc_file, 'w')

        f.write("### XPMIDI RC FILE. Autogenerated %s, do not modify.\n\n"
            % time.asctime())

        for o, t in options:
            if t == 'l' or t == 'i':     # lists are just converted
                pv = """%s""" % eval(o)
            elif t == 's':               # strings need additional love
                vv=eval(o)
                vv=vv.replace("'", "\\'")
                vv=vv.replace('"', '\\"')
                pv = """'%s'""" % vv
            f.write("%s = %s\n" % (o, pv))

        f.close()
        sys.exit()


    def playList(self):

        inpath = tkinter.filedialog.askopenfile(
            filetypes=[("Playlists","*.xpmidilst")], initialdir="~")

        if not inpath:
            return

        flist=[]
        dir=''
        while 1:
            l=inpath.readline()
            if not l:
                break
            l=l.strip()
            if l.startswith("#"):
                continue

            if l.upper().startswith("DIR:"):
                dir = l[4:]
            else:
                flist.append(os.path.join(dir, l))

        self.updateList(flist, 0)

    def updateList(self, files=None, sort=1, next=None):
        """ Update the list box with with midi files in the selected directories.

            1. If files is NOT None, it has to be a list of midi file names.
               If there are files, skip (2).
            2. Create a list of all the files with a .mid extension in all the dirs,
            3. Strip out the actual filename (less the mid ext) from each entry
               and create a dic entry with the filename as the key and the
               complete path as the data.
            4. Update the listbox
        """

        if not files:
            files=[]
            for f in current_dir:
                files.extend( glob.glob('%s/*.mid' % f))

        self.next_file_index = next

        self.fileList = {}  # dict of filenames indexed to display name
        tlist = []          # tmp list for dislay

        for f in files:
            a=f.split('/')[-1]  # get stuff after last '/'
            a=a.split('.')[-2]  # drop final (.mid) extension
            self.fileList[a]=f
            tlist.append(a)

        self.listbox.delete(0, END)

        if sort:
            tlist.sort()

        for f in tlist:
            self.listbox.insert(END, f)
            self.listbox.select_set(0)

        self.welcome()



###################################################
# Initial setup
####################################################


# Parse options.

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:],  "vf", [])
except getopt.GetoptError:
    usage()

for o,a in opts:
    if o == '-v':
        print(version)
        sys.exit(0)
    elif o == '-f':
        fullsize=1
    else:
        usage()

# Parse remaining cmd line params. This can be 1 directory name or
# a number of midi files.

fcount = 0
dcount = 0

for f in args:
    if os.path.isdir(f):
        dcount+=1
    elif os.path.isfile(f):
        fcount+=1
    else:
        print("%s is an Unknown filetype" % f)
        sys.exit(1)

if dcount and fcount:
    print("You can't mix filenames and directory names on the command line.")
    sys.exit(1)

if dcount > 1:
    print("Only 1 directory can be specified on the command line.")
    sys.exit(1)

# Read the RC file if it exists.

if os.path.exists(rc_file):
    try:
        exec(compile(open(rc_file).read(), rc_file, 'exec'))
    except IOError:
        print("Error reading %s:  %s" % (rc_file, sys.exc_info()[0]))

if not current_dir:
    current_dir = ['.']

# If a dir was specified make it current

if dcount:
    current_dir = [os.path.abspath(os.path.expanduser(args[0]))]


# Start the tk stuff. If you want to change the font size, do it here!!!

root = Tk()
root.title("Xpmidi+ - pmidi frontend")
if fullsize:
    root.geometry("%dx%s" % root.maxsize())
app=Application()

if fcount:
    app.updateList(args)

root.mainloop()
