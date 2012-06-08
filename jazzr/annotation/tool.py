from jazzr.rhythm import grid
from jazzr.midi import player

import curses, re, math

class Tool:

  ANNOTATING = 0
  PLAYING = 1
    
  def __init__(self, midifile, quarterspm=4, annotationfile=None):
    self.pos = 0.0
    self.notepos = 0
    self.padpos = 0
    self.maxdiv = 32
    self.midifile = midifile
    self.n = 1
    self.annotation = {}
    self.annotation['quarterspm'] = quarterspm
    self.track = track
    self.refreshGrid = True
    self.status = ''
    self.mode = self.ANNOTATING

  def setmaxdiv(self, maxdiv):
    if not maxdiv in [math.pow(2, i) for i in range(0, 8)]:
      return False
    self.maxdiv = maxdiv
    
  def units_per_quarternote(self):
    return 0.25 / (1/float(maxdiv))

  def midiscale(self):
    # Number of ticks per unit (specified by maxdiv)
    return midifile.quarternotes_to_ticks(1) / self.units_per_quarternote()

  def execute(self, match):
    props = match.groupdict()
    if 'action' in props:
      if props['action'] == 'q':
        return False
    return True

  def annotator(self):
    curses.wrapper(self.graphics)
    return self.onsets

  def curs_left(self): 
    pass

  def curs_right(self):
    pass

  def graphics(self, stdscr):
    #curses.halfdelay(10)
    self.my, self.mx = stdscr.getmaxyx()
    self.height = 9
    self.width = self.mx - 30
    self.posy = int(self.my / 2.0 - self.height / 2.0)
    self.posx = int(self.mx / 2.0 - self.width / 2.0)

    self.notepad = curses.newpad(self.height, self.n*self.maxdiv)
    self.com_buffer = curses.newwin(1, self.width, self.posy, self.posx)

    self.buf = ''
    #self.exp = re.compile('(?P<repetitions>[0-1]+)?(?P<command1>[adqpi ])|:(?P<command2>set) (numlevels) ([0-9]+)')
    exp = re.compile('(?P<repetitions>[0-9]+)?(?P<action>[adqri ])$|:(?P<command>set|play|stop|pause)(?P<arg1> numlevels)?(?P<arg2> [0-9]+)?$')
    annotate_exp = re.compile('([#b])?([a-g])([1-8])?') 

    while True:
      # Check if the buffer contains a command
      m = self.exp.match(self.buf)
      if m:
        if not self.execute(m):
          break
        self.buf = ''

      self.updateScr(stdscr)
      c = stdscr.getch()
      if c == curses.ERR: continue
      self.status = ''

      if c == 27: # or c == curses.KEY_BACKSPACE:
        # Empty buffer
        self.buf = ''
      elif c == curses.KEY_LEFT:
        self.curs_left()
      elif c == curses.KEY_RIGHT:
        self.curs_right()
      elif c == curses.KEY_UP:
        if self.mode == self.ANNOTATING:
          self.mode == self.PLAYING
      elif c == curses.KEY_DOWN:
        if self.mode == self.PLAYING:
          self.mode == self.ANNOTATING
      else:
        if c in range(32, 128):
          self.buf += chr(c)

  def updateScr(self, stdscr):
    # Refresh screen
    stdscr.clear()
    stdscr.addstr(self.posy+1+self.height, self.posx, 'Position: {0}\tMeasures: {1}\tNotes:{3}'.format(self.pos, self.n, len(self.annotation['notes'])))
    stdscr.addstr(self.posy+3+self.height, self.posx, 'Status: {0}'.format(self.status))
    stdscr.addstr(self.posy+5+self.height, self.posx, 'Gridposition: {0}'.format(self.pos))
    stdscr.refresh()
    # Refresh metrical grid
    if self.refreshGrid:
      notelist = self.generate_notelist()
      notestring = ' '.join(['{0}:{1}'.format(n[0], n[1]) for n in notelist])
      length = len(notelist)
      self.notepad.resize(self.height, length)
      self.notepad.clear()

      self.notepad.addstr(1, 0, notestr)
      self.refreshGrid = False

    if self.pos - self.padpos > self.width
      self.padpos += self.width / 2 
    elif self.pos - self.padpos < 0:
      self.padpos -= self.width / 2 

    metric_grid.refresh(0, self.padpos, self.posy+1, self.posx, self.posy+1+self.height, self.posx+self.width)
    stdscr.move(self.posy+1, self.posx+self.pos-self.padpos)

    # Refresh buffer display
    com_buffer.clear()
    com_buffer.addstr(0, 0, self.buf)
    com_buffer.refresh()

  def generate_notelist(self):
    notelist = []
    for note in self.midifile['1']:
      notelist.add((int(note.on / float(self.scale), note.name))
  

