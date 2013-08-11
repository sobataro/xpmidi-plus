#!/usr/bin/env python

from Tkinter import *
import tkSimpleDialog, tkFileDialog, tkMessageBox
import os, sys, signal, glob, time, getopt, shlex


# UGLY GLOBAL VARIABLES...

PlayPID = None        # PID of currently playing midi
DisplayPID = None     # PID for the display program

rcFile=os.path.expanduser("~/.xpmidirc")
Version = 3.4

fullsize = 0          # command line option for fullscreen

## These are stored in the rcfile on exit. Some can
## be modified via the options menu.

CurrentDir = ['.']
FavoriteDirs = []
player="aplaymidi"
PlayOpts = "-p 20:0"      # Player options
sysex = "GM"
Bcolor = "white"          # listbox colors
Fcolor = "medium blue"
killOnAbort = 1           # run "kill all notes" code on abort
displayProgram = ""
displayOptions = ""
displayDir = []

#############################################################

def usage():
    """ Display usage message and exit. """

    print "Xpmidi+, GUI frontend for MIDI Player"
    print "(c) 2003-12, Bob van der Poel"
    print "Usage: xpmidi [opts] [dir | Midifiles]"
    print "Options:"
    print "   -f    start full size"
    print "   -v    display version number"
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

def makeButtonBar(parent, row=0, column=0, buttons=(())):
    """ Create a single line frame with buttons. """

    bf=Frame(parent)
    c=0
    for txt, cmd in buttons:
        Button(bf, text=txt, height=1, command=cmd).grid(column=c, row=0, pady=5)
        c+=1
    bf.grid(row=row, column=column, sticky=W)
    return bf

def makeListBox(parent, width=50, height=20, selectmode=BROWSE, row=0, column=0):
    """ Create a list box with x and y scrollbars. """
    
    f=Frame(parent)
    ys=Scrollbar(f)
    xs=Scrollbar(f)
    lb=Listbox(f,
               bg=Bcolor,
               fg=Fcolor,
               width=width,
               height=height,
               yscrollcommand=ys.set,
               xscrollcommand=xs.set,
               exportselection=FALSE,
               selectmode=selectmode )

    ys.config(orient=VERTICAL, command=lb.yview)
    ys.grid(column=0,row=0, sticky=N+S)

    xs.config(orient=HORIZONTAL, command=lb.xview)
    xs.grid(column=1, row=1, sticky=E+W)

    lb.grid(column=1,row=0, sticky=N+E+W+S)

    f.grid(row=row, column=column, sticky=E+W+N+S) 
    f.grid_rowconfigure(0, weight=1)   
    f.grid_columnconfigure(1, weight=1)
    
    return  lb

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

        if PlayPID:
            return

        self.f=f=Toplevel()
        if root.winfo_viewable():
            f.transient(root)
 
        makeMenu(f, buttons=(
            ("Cancel", self.f.destroy), ("Apply", self.apply)))
        self.playerEnt =  makeEntry(f, label="MIDI Player",      text=player,   row=1)
        self.playOptEnt = makeEntry(f, label="Player Options",   text=PlayOpts, row=2) 
        self.sysexEnt =   makeEntry(f, label="SysEX",            text=sysex,    row=3)
        self.playerAbort = makeEntry(f, label="Kill notes on abort", text=killOnAbort, row=4)
        self.fgEnt =      makeEntry(f, label="Foreground Color", text=Fcolor,   row=5)
        self.bgEnt =      makeEntry(f, label="Background Color", text=Bcolor,   row=6)

        self.displayPrg = makeEntry(f, label="PDF Display", text=displayProgram, row=7)
        self.displayOpt = makeEntry(f, label="PDF Options", text=displayOptions, row=8)
        self.displayPath = makeEntry(f, label="PDF Path", text=', '.join(displayDir), row=9)

        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)

       	f.grab_set()
	root.wait_window(f)	

 
    def apply(self): 
        global player, PlayOpts, sysex, killOnAbort
        global Fcolor, Bcolor
        global displayProgram, displayOptions, displayDir

        player = self.playerEnt.get()
        PlayOpts = self.playOptEnt.get()
        sysex = self.sysexEnt.get()

        killOnAbort = self.playerAbort.get()
        if killOnAbort.upper() in ("YES", "ON", "1"):
            killOnAbort = 1
        else:
            killOnAbort = 0

        displayProgram = self.displayPrg.get()
        displayOptions = self.displayOpt.get()
        fg = self.fgEnt.get()
        bg = self.bgEnt.get()

        try:
            app.lb.config(fg=fg)
            Fcolor = fg
        except TclError:
            tkMessageBox.showerror("Set Forground Color", "Illegal foreground color value")

        try:
            app.lb.config(bg=bg)
            Bcolor = bg
        except TclError:
            tkMessageBox.showerror("Set Background Color", "Illegal background color value")

        self.f.destroy()


########################################
# A listbox with the favorites directory

class selectFav(object):

    def __init__(self):

#        if PlayPID:
#            return

        self.f=f=Toplevel()
        if root.winfo_viewable():  
            f.transient(root)

        makeMenu(f, buttons=(
            ("Open", self.select),
            ("Add Current", self.addToFav),
            ("Delete", self.delete)))
      
        self.lb = lb = makeListBox(f, height=10, selectmode=MULTIPLE, row=2, column=0)
        lb.bind("<Double-Button-1>", self.dclick)
        
        # Make the listbox frame expandable

        f.grid_rowconfigure(2, weight=1)
        f.grid_columnconfigure(0, weight=1)

        self.updateBox()

        f.grab_set()
        f.focus_set()
        f.wait_window(f)



    def dclick(self, w):
        """ Callback for doubleclick. Just do one dir. """

        self.doSelect( [self.lb.get(self.lb.nearest(w.y))] )


    def select(self):
        """ Callback for the 'select' button. """

        l=[]
        for n in self.lb.curselection():
            l.append(self.lb.get(int(n)))
        self.doSelect(l)


    def doSelect(self, n):
        """ Update the filelist. Called from select button or doubleclick."""

        global CurrentDir

        if n:
            CurrentDir = n
            app.updateList()
        self.f.destroy()


    def addToFav(self):
        """ Add the current directory (what's displayed) to favorites."""

        for n in CurrentDir:
            if n and not FavoriteDirs.count(n):
                FavoriteDirs.append(n)

        FavoriteDirs.sort()
        self.updateBox()

    def delete(self):
        """ Delete highlighted items, Called from 'delete' button. """

        global FavoriteDirs

        l=[]
        for n in self.lb.curselection():
            l.append(self.lb.get(int(n)))

        if l:
            if tkMessageBox.askyesno("Delete Directory",
                     "Are you sure you want to delete the "
                     "highlighted directories from the favorites list?",
                      parent=self.f):

                for n in l:
                    FavoriteDirs.remove(n)

                self.updateBox()


    def updateBox(self):
        global FavoriteDirs

        self.lb.delete(0, END)
        for n in FavoriteDirs:
            self.lb.insert(END, n)


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
             ("Stop", self.stopPmidi ),
             ("Open Dir", self.chd),
             ("Load Playlist", self.playList),
             ("Favorites", selectFav ),
             ("Options", setOptions ) ) )

        self.msgbox = makeLabelBox(root, justify=LEFT, row=2, column=0)

        self.lb=lb = makeListBox(root, height=28, row=1, column=0)

        self.elasped = 0
       
        # Make the listbox frame expandable
        
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # some bindings 

        lb.bind("<Return>",  self.loadfileRet)
        lb.bind("<Double-1>", self.loadfileDoubleClick)

        lb.bind('<Button-3>', self.stopPmidi)
        root.bind('<Escape>', self.stopPmidi)

        root.protocol("WM_DELETE_WINDOW", self.quitall)

        for a in 'abcdefghijklmnopqrstuvwxyz':
            root.bind(a, self.keyPress)

        lb.bind('<F1>', self.displayOnly)
        lb.bind('<F2>', self.rotateDisplayList)

        # end bindings

        lb.focus_force()   # make the listbox use keyboard

        self.CurrentFile = None
        self.fileList = {}    # dict of files in listbox. Key is displayed name, data=actual

        self.updateList()
        self.welcome()

    def welcome(self):
        """ Display (c) message in status box. """

        if CurrentDir:
            c=', '.join(CurrentDir)
        else:
            c = ' '
        self.msgbox.config(text="XPmidi+\n%s" % c)

    lastkey = ''
    lastkeytime = 0

    def keyPress(self, ev):
        """ Callback for the alpha keys a..z. Finds 1st entry matching keypress. """

        c=self.lastKeyHit = ev.char.upper()

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

        l=self.lb.get(0, END)

        for x,a in enumerate(l):
            if a[0:sz].upper() >= c:
                self.lb.select_clear(ACTIVE)   # needed to un-hilite existing selection
                self.lb.activate(x)
                self.lb.see(x)
                self.lb.select_set(x)
                break
    


    """ Play a selected file. This is a listbox callback. 
        Two callback funcs are needed: one for a mouse click,
        the other for a <Return>.
    """

    def loadfileRet(self, w):
        """ Callback for <Return>. """

        self.loadfile(self.lb.get(ACTIVE) )

    def loadfileDoubleClick(self, w):
        """ Callback for <Double-1>. """

        self.lb.activate(self.lb.nearest(w.y))
        self.loadfile(self.lb.get(self.lb.nearest(w.y)))
            
    def loadfile(self, f):
        global PlayPID

        if not f:
            return

        f=self.fileList[f]
        self.stopPmidi()

        self.displayPDF(f)
        PlayPID = self.playfile(f)
        
        self.CurrentFile = f.split('/')[-1]

        root.update()


    def checkfor(self):
        """ Callback for the "after" timer."""

        global PlayPID, DisplayPID

        t = time.time() - self.playTimer
        self.msgbox.config(text="[%02d:%02d]: %s\n%s" % (int(t/60), int(t % 60), self.CurrentFile, CurrentDir[0]))

        if DisplayPID:
            try:
                os.waitpid(DisplayPID, os.WNOHANG)
            except OSError:   # our display is gone, kill the player
                DisplayPID = None
                self.stopPmidi()

        if PlayPID:
            try:
                s = os.waitpid(PlayPID, os.WNOHANG)
                root.after(500, self.checkfor)
            except OSError:  # player is gone, kill display
                if DisplayPID:
                    os.kill(DisplayPID, signal.SIGKILL) 
                DisplayPID = None
                PlayPID = None
                self.playTimer = 0
                self.welcome()

    def stopPmidi(self, w=''):
        """ Stop currently playing MIDI. """

        global PlayPID, DisplayPID

        if not PlayPID and not DisplayPID:    # nothing playing, just return
            return

        if DisplayPID:
            os.kill(DisplayPID, signal.SIGKILL)
            DisplayPID = None

        cPID = PlayPID
        PlayPID = None

        self.msgbox.config(text="Stopping...%s\n" % self.CurrentFile)
        root.update_idletasks()

        """ See if last run is still running. The call to os.waitpid()
            returns a process ID and a status indication. We check the PID
            returned. If this value is equal to the current PID then
            the process has died ... and we can ignore the whole issue.
        """ 
        
        if cPID:

            try:
                pid,s = os.waitpid(cPID, os.WNOHANG)
            except OSError:
                return

            if pid:
                return

            x=os.kill(cPID, signal.SIGKILL)  # stop current player, could leave hanging notes

            if killOnAbort:
                # Create a standard MIDI file which sets all notes OFF.

                tempfile = '/tmp/xpmidi-reset.mid'
                f=open(tempfile, 'w')

                # Standard midi file header, track count=1
                f.write( "MThd" + chr(0) + chr(0) + chr(0) + chr(6) + chr(0) + chr(1) + \
                     chr(0) + chr(1) + chr(0) +chr(0xc0) )

                # select sysex
                if sysex == "XG":
                    # XG System On
                    sysex_list = [0x00, 0xf0, 0x08,
                        0x43, 0x10, 0x4C, 0x00, 0x00, 0x7e, 0x00, 0xf7]
                elif sysex == "GS":
                    # GS Reset
                    sysex_list = [0x00, 0xf0, 0x0a,
                        0x41, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7f, 0x00,
                        0x41, 0xF7]
                else:
                    # GM System On
                    sysex_list = [0x00, 0xf0, 0x05,
                        0x7e, 0x7f, 0x09, 0x01, 0xf7]
                
                # track header and length
                f.write("MTrk" + chr(0) + chr(0) + chr(0))
                f.write(chr(4 + len(sysex_list)))
                
                # write sysex
                for byte in sysex_list:
                    f.write(chr(byte))

                # EOF status event (4 tick offset) (4)
                f.write( chr(4) + chr(0xff) + chr(0x2f) + chr(0) )
                f.close()

                self.playfile(tempfile, wait=os.P_WAIT)

                os.remove(tempfile)
                time.sleep(.5)

        self.welcome()


    def playfile(self, f, wait=os.P_NOWAIT):
        """ Call the midi player. Used by loadfile() and stoppmidi(). """


        root.after(500, self.checkfor)
        self.playTimer = time.time()
        
        # 3rd arg is a list! Player name, options and filename.
        
        ##a=os.spawnvp(os.P_NOWAIT, "sync", []) # avoid delays while playing (maybe!)
        
        op = shlex.split(PlayOpts)

        return os.spawnvp(wait, player, [player] + op + [f]  ) 

    # PDF display

    def rotateDisplayList(self, w):
        """ Callback for <F2>. Rotate display PDF list"""

        global displayDir
        if not len(displayDir):
            return

        displayDir.append(displayDir.pop(0))
        opts={'aspect':4}
        tkMessageBox.showinfo(message="DisplayPDF dir: %s" % displayDir[0])
        
    def displayOnly(self, w):
        """ Callback for <F1>. """

        self.stopPmidi()
        self.displayPDF(self.fileList[self.lb.get(ACTIVE)] )

    def displayPDF(self, midifile):
        """ Find and display a PDF for the currently playing file. """

        global DisplayPID

        if not displayProgram:
            return
        
        if DisplayPID:
            os.kill(DisplayPID, signal.SIGKILL)
            
        f = os.path.basename(midifile).replace(".mid", ".pdf")
        if len(displayDir):
            t = os.path.join(os.path.expanduser(displayDir[0]), f)
            if os.path.exists(t):
                DisplayPID = os.spawnvp(os.P_NOWAIT, displayProgram, [displayProgram] \
                        + displayOptions.split() + [t]  )
        else:
            displayPID = None


    def chd(self):
        """ Callback from <Open Dir> button. Switch to new directory and updates list.  """

        global CurrentDir

        if PlayPID:
            return

        d=tkFileDialog.askdirectory(initialdir=','.join(CurrentDir))

        if d:
            CurrentDir = [d]
            app.updateList()



    def quitall(self, ex=''):
        """ All done. Save current dir, stop playing and exit. """

        self.stopPmidi()

        def writeoption(s):
            print "%s = %s" % (s, eval(s))

        # The options by name and a 'type': 'list', 'string', 'integer'
        options = [
            ['FavoriteDirs',   'l'],
            ['CurrentDir',     'l'],
            ['Bcolor',         's'],
            ['Fcolor',         's'],
            ['PlayOpts',       's'],
            ['player',         's'],
            ['sysex',          's'],
            ['killOnAbort',    'i'],
            ['displayProgram', 's'],
            ['displayOptions', 's'],
            ['displayDir',     'l']  ]

        f=open(rcFile, 'w')
        
        f.write("### XPMIDI RC FILE. Autogenerated %s, do not modify.\n\n" % time.asctime())

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

        inpath = tkFileDialog.askopenfile(filetypes=[("Playlists","*.xpmidilst")],
          initialdir="~")

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
        
    def updateList(self, files=None, sort=1):
        """ Update the list box with with midi files in the selected directories.
    
            1. If files is NOT None, it has to be a list of midi file names. If
               there are files, skip (2).
            2. Create a list of all the files with a .mid extension in all the dirs,
            3. Strip out the actual filename (less the mid ext) from each entry
               and create a dic entry with the filename as the key and the complete
               path as the data.
            4. Update the listbox 
        """

        if not files:
            files=[]
            for f in CurrentDir:
                files.extend( glob.glob('%s/*.mid' % f))

        self.fileList = {}  # dict of filenames indexed to display name
        tlist = []          # tmp list for dislay

        for f in files:
            a=f.split('/')[-1]  # get stuff after last '/'
            a=a.split('.')[-2]  # drop final (.mid) extension
            self.fileList[a]=f
            tlist.append(a)

        self.lb.delete(0, END)

        if sort:
            tlist.sort()
       
        for f in tlist:
            self.lb.insert(END, f)
            self.lb.select_set(0)
        
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
        print Version
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
        print "%s is an Unknown filetype" % f
        sys.exit(1)

if dcount and fcount:
    print "You can't mix filenames and directory names on the command line."
    sys.exit(1)

if dcount > 1:
    print "Only 1 directory can be specified on the command line."
    sys.exit(1)

# Read the RC file if it exists.

if os.path.exists(rcFile):
    try:
        execfile( rcFile )
    except IOError:
        print "Error reading %s:  %s" % (rcFile, sys.exc_info()[0] )

if not CurrentDir:
    CurrentDir = ['.']

# If a dir was specified make it current

if dcount:
    CurrentDir = [os.path.abspath(os.path.expanduser(args[0]))]


# Start the tk stuff. If you want to change the font size, do it here!!!

root = Tk()
root.title("Xpmidi+ - pmidi frontend")
root.option_add('*font', "Arial 10")
if fullsize:
    root.geometry("%dx%s" % root.maxsize())
app=Application()

if fcount:
    app.updateList(args)

root.mainloop()




