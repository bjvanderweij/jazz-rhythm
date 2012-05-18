from pygame import midi
import tools, time, corpus, math
import curses, curses.wrapper, threading, cgui
from collections import deque

class Sequencer(threading.Thread):

  LOADFILE = 0
  LOADTRACK = 1
  SETOUTPUT = 2
  PLAY = 3
  STOP = 4
  IDLE = 5
  PAUSE = 6
  SETSPEED = 7

  PLAYING = 0
  PAUSED = 1

  def __init__(self, lock, midiplayer):
    self.running = False
    self.stopped = False
    self.midiplayer = midiplayer

    self.lock = lock

    self.midifile = None
    self.events = None
    self.currentdevice = 0
    self.currenttrack = 0
    self.time = 0
    self.mode = self.PAUSED

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
      self.midiplayer.stop = True
      raise
    finally:
      midi.quit()

  def runthread(self):
    out = None
    self.running = True

    nexttime = timeleft = i = 0
    # Timestep in seconds
    dt = 1/20.0
    speed = 1.0
    on = {}
    self.status = 'Running'


    while self.running:
     
      if not self.mode == self.PLAYING:
        for pitch in on.keys():
          out.note_off(int(pitch), 64, 0)
        on = {}
        time.sleep(0.1)

      action, arg = (None, None)
      self.lock.acquire()
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
        nexttime = timeleft = i = 0
        self.mode = self.PAUSED
      elif action == self.LOADTRACK:
        self.status = 'Loading track'
        self.events = self.midifile[arg].toEvents()
        nexttime = timeleft = i = 0
        self.currenttrack = arg
        self.status = 'Track loaded'
      elif action == self.STOP:
        self.status = 'Stopped'
        self.mode = self.PAUSED
        nexttime = timeleft = i = 0
        self.time = 0
      elif action == self.SETOUTPUT:
        if out:
          out.close()
        out = midi.Output(int(arg))
        self.currentdevice = arg
      elif action == self.SETSPEED:
        speed = arg
      elif action == self.PAUSE:
        self.status = 'Paused'
        self.mode = self.PAUSED
      elif action == self.PLAY:
        if not self.midifile:
          self.status = 'Load a file first'
        elif not self.events:
          self.status = 'Load a track first'
        elif not out:
          self.status = 'Select an output first'
        else:
          self.mode = self.PLAYING
          self.status = 'Playing'

      if self.mode == self.PLAYING:

        self.time = nexttime - timeleft
        if timeleft > dt:
          time.sleep(dt/speed)
          timeleft -= dt
          continue
        
        time.sleep(timeleft/speed)

        if i == 0: 
          i = 1
          timeleft = self.midifile.ticks_to_seconds(self.events[i][0]) 
          nexttime = timeleft
          continue

        e = self.events[i-1]
        next_e = self.events[i]
        nexttime = self.midifile.ticks_to_seconds(next_e[0]) 
        # Calculate the time difference and convert to seconds
        ticks = next_e[0] - e[0]
        timeleft = self.midifile.ticks_to_seconds(ticks)
        
        if e[3] is 'on':
          out.note_on(e[1], e[2], 0)
          on[str(e[1])] = 1
        elif e[3] is 'off':
          # Sometimes note_offs are lost? 
          # Unbelievably sending twice reduces this.
          out.note_off(e[1], e[2], 0)
          out.note_off(e[1], e[2], 0)
          if str(e[1]) in on:
            del on[str(e[1])]
        elif e[3] is 'patch_change':
          out.patch_change(e[1], e[2])


        if i < len(self.events) - 1:
          i += 1
        else:
          self.control(self.STOP, None)

    #if out:
      # Blocks?
      #out.eof()
      #out.close()

    self.stopped = True

class MidiPlayer:


  def __init__(self):
    self.stop = False
    self.stopped = False
    self.seq = None
    self.lock = threading.Lock()

  def startgui(self):
    if not self.seq:
      self.seq = Sequencer(self.lock, self)
      self.seq.start()
    try:
      curses.wrapper(self.gui)
    except Exception:
      import sys
      print "Unexpected error:", sys.exc_info()[0]
      raise
      raise Exception
    finally:
      print "Stopping sequencer thread"
      self.seq.running = False
      while not self.seq.stopped: time.sleep(0.1)

  def startcommandline(self):
    if not self.seq:
      self.seq = Sequencer(self.lock, self)
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
      while not self.seq.stopped: time.sleep(0.1)

  def play(self, midifile, track):
    if not self.seq:
      self.seq = Sequencer(self.lock, self)
      self.seq.start()
    self.seq.control(self.seq.LOADFILE, midifile)
    self.seq.control(self.seq.LOADTRACK, track)
    self.seq.control(self.seq.SETOUTPUT, 0)
    self.seq.control(self.seq.PLAY, None)
    self.startcommandline()

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
      elif inp == 'track' or inp == 't':
        if seq.midifile:
          choice = tools.menu('Choose a track',\
             ['Track #{0}.\tName: {1}\tNumber of notes: {2}'.format(\
              seq.midifile[t].n, seq.midifile[t].name, len(seq.midifile[t]))\
              for t in seq.tracklist()])
          if choice < 0: continue
          seq.control(seq.LOADTRACK, seq.tracklist()[choice])
      elif inp == 'load' or inp == 'f':
        choice = tools.menu('Choose a file', sorted(corpus.names()))
        if choice < 0: continue
        print 'Loading file'
        seq.control(seq.LOADFILE, corpus.loadname(sorted(corpus.names())[choice]))
      elif inp == 'output' or inp == 'device' or inp == 'd' or inp == 'o':
        choice = tools.menu('Choose a midi device', seq.devicelist())
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
      # Emergency stop
      if self.stop:
        break
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
      elif c == ord('f'):
        choice = cgui.cmenu(stdscr, 'Choose a file', sorted(corpus.names()))
        if choice < 0: continue
        cgui.calert(stdscr, 'Loading file')
        seq.control(seq.LOADFILE, corpus.loadname(sorted(corpus.names())[choice]))
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
    self.stopped = True

if __name__ == '__main__':
  mp = MidiPlayer()
  mp.startgui()
#out.write([[[0x9, 50, 80], 0],[[0x9, 53, 80], 500],[[0x8, 53, 0], 1500],[[0x, 50, 0], 2000]])
