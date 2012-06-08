from pygame import midi
from collections import deque
from jazzr.tools import commandline, cgui
from jazzr.corpus import files
import time, math, curses, threading

class Sequencer(threading.Thread):

  LOADFILE = 0
  LOADTRACK = 1
  SETOUTPUT = 2
  PLAY = 3
  STOP = 4
  IDLE = 5
  PAUSE = 6
  SETSPEED = 7
  NEXTNOTE = 8
  GOTO = 9
  SETTIME = 10

  PLAYING = 0
  PAUSED = 1
  ONENOTE = 2

  def __init__(self, selfdestruct=False):
    self.running = False

    self.selfdestruct=selfdestruct

    self.lock = threading.Lock()

    self.midifile = None
    self.events = None
    self.currentdevice = 0
    self.currenttrack = 0
    self.mode = self.PAUSED
    self.out = None

    # Timestep in seconds
    self.dt = 1/20.0
    self.speed = 1.0
    self.on = {}
    self.time = 0

    self.status = 'Not started'
    self.do = deque()

    threading.Thread.__init__(self)

  def devicelist(self):
    devices = []
    for i in range(midi.get_count()):
      info = midi.get_device_info(i)
      devices.append("{0}, {1}, Input:{2}, Output:{3}".format(info[0], info[1], info[2], info[3]))
    return devices

  def device_info(self):
    return midi.get_device_info(int(self.currentdevice))

  def tracklist(self):
    return [str(t) for t in sorted([int(x) for x in self.midifile.keys()])]
    

  # Thread safe way to send messages to the sequencer
  def control(self, action, arg):
    self.lock.acquire()
    # Append to queue
    self.do.append((action, arg))
    self.lock.release()

  def run(self):
    try:
      midi.init()
      self.runthread()
    except:
      raise
    finally:
      if self.out:
        self.notesoff()
        self.out.close()
      midi.quit()
      self.running = False

  def notesoff(self):
    for pitch in self.on.keys():
      self.out.note_off(int(pitch), 64, 0)
    self.on = {}

  def runthread(self):
    self.running = True

    nextevent = pos = 0
    self.time = 0
    self.status = 'Running'

    while self.running:
     
      if not self.mode == self.PLAYING:
        self.notesoff()
        time.sleep(0.1)

      action, arg = (None, None)
      self.lock.acquire()
      if len(self.do) == 0 and not self.mode == self.PLAYING and self.selfdestruct:
        self.lock.release()
        break
      if len(self.do) > 0 :
        # Pop from queue
        #print 'Sequencer: Queue: {0}'.format(self.do)
        action, arg = self.do.popleft()
        #print 'Sequencer: Executing {0}'.format((action, arg))
      self.lock.release()

      if not action:
        pass
      if action == self.LOADFILE:
        self.midifile = arg
        nextevent = pos = 0
        self.time = 0
        self.mode = self.PAUSED
        self.events = None
      elif action == self.LOADTRACK:
        self.status = 'Loading track'
        self.events = self.midifile[str(arg)].toEvents()
        nextevent = pos = 0
        self.time = 0
        self.currenttrack = arg
        self.status = 'Track loaded'
      elif action == self.STOP:
        self.status = 'Stopped'
        self.mode = self.PAUSED
        nextevent = pos = 0
        self.time = 0
      elif action == self.SETOUTPUT:
        if self.out:
          self.out.close()
        self.out = midi.Output(int(arg))
        self.currentdevice = arg
      elif action == self.SETTIME:
        if not self.midifile: continue
        if arg < 0:
          pos = nextevent = self.time = 0
          continue
        if arg > self.midifile.ticks_to_seconds(self.events[-1][0]):
          self.control(self.STOP, None)
          continue
        for i in range(0, len(self.events)):
          if arg <= self.midifile.ticks_to_seconds(self.events[i][0]):
            nextevent = self.midifile.ticks_to_seconds(self.events[i][0])
            pos = i
            break
        self.time = arg
        self.notesoff()
      elif action == self.SETSPEED:
        self.speed = arg
      elif action == self.GOTO:
        pos = arg
      elif action == self.PAUSE:
        self.status = 'Paused'
        self.mode = self.PAUSED
      elif action == self.PLAY:
        if not self.midifile:
          self.status = 'Load a file first'
        elif not self.events:
          self.status = 'Load a track first'
        elif not self.out:
          self.status = 'Select an output first'
        else:
          self.mode = self.PLAYING
          self.status = 'Playing'

      if self.mode == self.PLAYING or self.mode == self.ONENOTE:

        if pos == 0:
          nextevent = self.midifile.ticks_to_seconds(self.events[pos][0]) 
        timeleft = nextevent - self.time
        if timeleft > self.dt:
          time.sleep(self.dt/self.speed)
          self.time += self.dt
          continue
        
        time.sleep(timeleft/self.speed)
        self.time += timeleft

        timeleft = nextevent = 0
        if pos+1 < len(self.events):
          nextevent = self.midifile.ticks_to_seconds(self.events[pos+1][0]) 
        
        e = self.events[pos]
        if e[3] is 'on':
          self.out.note_on(e[1], e[2], 0)
          self.on[str(e[1])] = 1
        elif e[3] is 'off':
          # Sometimes note_offs are lost? 
          # Sending twice reduces this.
          self.out.note_off(e[1], e[2], 0)
          self.out.note_off(e[1], e[2], 0)
          if str(e[1]) in self.on:
            del self.on[str(e[1])]
        elif e[3] is 'patch_change':
          self.out.patch_change(e[1], e[2])


        if pos+1 < len(self.events):
          pos += 1
        elif self.selfdestruct:
          break
        else:
          self.control(self.STOP, None)

    self.notesoff()

class Player:


  def __init__(self):
    self.stop = False
    self.seq = None

  def startgui(self):
    if not self.seq:
      self.seq = Sequencer()
      self.seq.start()
    try:
      print "Starting gui"
      curses.wrapper(self.gui)
    except Exception:
      import sys
      print "Unexpected error:", sys.exc_info()[0]
      raise
      raise Exception
    finally:
      print "Stopping sequencer thread"
      self.seq.running = False

  def startcommandline(self):
    if not self.seq:
      self.seq = Sequencer()
      self.seq.start()
    try:
      self.commandline()
    except Exception:
      import sys
      print "Unexpected error:", sys.exc_info()[0]
      raise
      raise Exception
    finally:
      print "Stopping sequencer thread"
      self.seq.running = False

  def play(self, midifile, track, gui=False, block=True):
    if not self.seq:
      self.seq = Sequencer()
      self.seq.start()
    self.seq.control(self.seq.LOADFILE, midifile)
    self.seq.control(self.seq.LOADTRACK, track)
    self.seq.control(self.seq.SETOUTPUT, 0)
    self.seq.control(self.seq.PLAY, None)
    if not block:
      return self.seq
    if gui:
      self.startgui()
    return self.seq

  def commandline(self):
    seq = self.seq
    inp = ''

    print 'Command line midi player. Type help for a list of commands'
    while inp is not 0 and inp is not 'exit':

      try: inp = raw_input(':')
      except(EOFError, KeyboardInterrupt):
        print
        break

      if inp == 'stop':
        seq.control(seq.STOP, None)
      elif inp == 'play' or inp == 'p':
        seq.control(seq.PLAY, None)
      elif inp == 'metricality' or inp == 'm':
        seq.midifile[str(seq.currenttrack)].isMetrical()
      elif inp == 'pause':
        seq.control(seq.PAUSE, None)
      elif inp == 'status' or inp == 's':
        print seq.status
      elif inp == 'h':
        seq.control(seq.SETTIME, seq.time-1)
      elif inp == 'l':
        seq.control(seq.SETTIME, seq.time+1)
      elif inp == 'track' or inp == 't':
        if seq.midifile:
          choice = commandline.menu('Choose a track',\
             ['Track #{0}.\tName: {1}\tNumber of notes: {2}'.format(\
              seq.midifile[t].n, seq.midifile[t].name, len(seq.midifile[t]))\
              for t in seq.tracklist()])
          if choice < 0: continue
          seq.control(seq.LOADTRACK, seq.tracklist()[choice])
      elif inp == 'load' or inp == 'f':
        choice = commandline.menu('Choose a file', sorted(files.names()))
        if choice < 0: continue
        print 'Loading file'
        seq.control(seq.LOADFILE, files.loadname(sorted(files.names())[choice]))
      elif inp == 'output' or inp == 'device' or inp == 'd' or inp == 'o':
        choice = commandline.menu('Choose a midi device', seq.devicelist())
        if choice < 0: continue
        seq.control(seq.SETOUTPUT, choice)



  def gui(self, stdscr):
    seq = self.seq
    my, mx = stdscr.getmaxyx()
   
    #curses.mousemask(curses.BUTTON1_CLICKED)
    curses.halfdelay(1)
    y = x = 0
    scale = 10
    time = 0.0
    tracks = None
    length = None
    viewpos = 0
    trackview = None
    viewwidth = mx - 9 - 3
    maxscale = 100
    speed = 1.0
    following = True
    name = None
    while True:
      if not seq.running:
        pass
        #break
      stdscr.clear()
      curses.curs_set(0)
      stdscr.addstr(0, 0, '[(p)lay/pause] [(s)top] [choose (f)ile] [choose (t)rack] [choose (o)utput] [((j/k) slower/faster)] [toggle (F)ollowing]')
      stdscr.addstr(1, 0, '[(e)dit alignment] [e(x)port track]')
      if seq.midifile:
        stdscr.addstr(4, 3, 'File: {0}'.format(seq.midifile.name))
        stdscr.addstr(5, 3, 'Midi Device: {0}'.format(seq.device_info()))
        stdscr.addstr(6, 3, 'Midi Track: {0}'.format(seq.currenttrack))
      stdscr.addstr(7, 3, 'Player status: {0}'.format(seq.status))

      stdscr.refresh()
      
      time = self.seq.time
      
      # Load tracks once the midifile is loaded
      if self.seq.midifile and name is not self.seq.midifile.name:
        name = self.seq.midifile.name
        tracks = []
        for t in self.seq.midifile.values():
          if len(t) > 0:
            tracks.append(t)
        tracks = sorted(tracks, key=lambda x: x.n)
        length = max([t.length() for t in tracks])
        length /= 1000000.0
        trackview = None

      # Paint the trackview
      if tracks and not trackview:
        trackview = \
          cgui.trackview(stdscr, tracks, ypos=9, xpos=3, width=viewwidth, scale=scale)
        viewpos = 0

      if tracks and trackview:
        if seq.mode == seq.PLAYING and following:
          if time*scale < round(viewwidth/2.0):
            viewpos = 0
          elif time*scale > length*scale - round(viewwidth/2.0):
            viewpos = length*scale - viewwidth
          else:
            viewpos = time*scale - round(viewwidth/2.0)
            
        cgui.updatetracks(stdscr, viewpos, time, trackview, ypos=9, xpos=3, width=mx-10, scale=scale, currenttrack=seq.currenttrack)
        stdscr.addstr(len(tracks)+1+9, 3, 'Time: {0:.2f}\tTime left: {1:.2f}\tTrackview scale: {2}\tSpeed: {3}' .format(time, length-time, scale, speed))

      c = stdscr.getch()

#      if c == curses.KEY_MOUSE:
#        (id, x, y, z, state) = curses.getmouse()
#        if state == curses.BUTTON1_CLICKED:
#          pass
#
      if c == ord('q'):
        seq.running = False
        break
      elif c == ord('F'):
        if following:
          following = False
        else:
          following = True
      elif c == ord('s'):
        seq.control(seq.STOP, None)
      elif c == ord('N'):
        seq.control(seq.NEXTNOTE, None)
      elif c == ord('p'):
        if seq.mode == seq.PLAYING:
          seq.control(seq.PAUSE, None)
        else:
          seq.control(seq.PLAY, None)
      elif c == ord('t'):
        if seq.midifile:
          choice = cgui.cmenu(stdscr, 'Choose a track',\
              ['Track #{0}\tName: {1}\tNumber of notes: {2}'.format(\
              seq.midifile[t].n, seq.midifile[t].name, len(seq.midifile[t]))\
              for t in seq.tracklist()])
          if choice < 0: continue
          seq.control(seq.LOADTRACK, seq.tracklist()[choice])
      elif c == ord('j'):
        if speed > 0:
          speed -= 0.01
        seq.control(seq.SETSPEED, speed)
      elif c == ord('k'):
        speed += 0.01
        seq.control(seq.SETSPEED, speed)
      elif c == ord('h'):
        seq.control(seq.SETTIME, seq.time-1)
      elif c == ord('l'):
        seq.control(seq.SETTIME, seq.time+1)
      elif c == ord('f'):
        level = 1
        midifile = None
        while level > 0:
          if level == 1:   
            choice = cgui.cmenu(stdscr, 'Choose collection', files.collections())
            if choice == -1:
              level -= 1
              continue
            else: level += 1
            collection = files.collections()[choice]
          elif level == 2:   
            choice = cgui.cmenu(stdscr, 'Choose song', files.songs(collection=collection))
            if choice == -1:
              level -= 1
              continue
            else: level += 1
            song = files.songs(collection=collection)[choice]
          elif level == 3:   
            choice = cgui.cmenu(stdscr, 'Choose version', files.versions(song, collection=collection))
            if choice == -1: 
              level -= 1
              continue
            else: level += 1
            version = files.versions(song, collection=collection)[choice]
          elif level == 4:   
            singletrack = False
            track = 0
            if len(files.tracks(song, version, collection=collection)) > 0:
              singletrack = True
              choice = cgui.cmenu(stdscr, 'Choose track', files.tracks(song, version, collection=collection))
              if choice == -1:
                level -= 1
                continue
              else: level += 1
              track = files.tracks(song, version, collection=collection)[choice]
            midifile = files.load(song, version, track, singletrack, collection=collection)
            break
        if not midifile: continue
        #choice = cgui.cmenu(stdscr, 'Choose a file', sorted(files.paths()))
        #if choice < 0: continue
        cgui.calert(stdscr, 'Loading file')
        #seq.control(seq.LOADFILE, files.loadname(sorted(files.paths())[choice]))
        seq.control(seq.LOADFILE, midifile)
        time = 0
      elif c == ord('o'):
        choice = cgui.cmenu(stdscr, 'Choose a midi device', seq.devicelist())
        if choice < 0: continue
        seq.control(seq.SETOUTPUT, choice)
      elif c == curses.KEY_LEFT:
        if viewpos > 0:
          viewpos -= 1
      elif c == curses.KEY_RIGHT:
        if viewpos < length*scale - viewwidth:
          viewpos += 1
      elif c == curses.KEY_UP:
        if scale < maxscale and trackview:
          scale += 1
          trackview = \
            cgui.trackview(stdscr, tracks, ypos=9, xpos=3, width=viewwidth, scale=scale)
      elif c == curses.KEY_DOWN:
        if scale > 1 and trackview:
          scale -= 1
          trackview = \
            cgui.trackview(stdscr, tracks, ypos=9, xpos=3, width=viewwidth, scale=scale)
    curses.endwin()
