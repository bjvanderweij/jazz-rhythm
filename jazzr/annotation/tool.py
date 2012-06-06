from jazzr.rhythm import grid

import curses, re

class Tool:

  def __init__(self):
    self.numlevels = 4
    self.n = 1
    self.level = 0
    self.pos = 0.0
    self.gridpos = 0
    self.onsets = []
    self.refreshGrid = True
    self.status = ''
  
  def execute(self, match):
    props = match.groupdict()
    if props['command1']:
      command = props['command1']
    else:
      command = props['command2']
    repetitions = 1

    if props['repetitions']: repetitions = int(props['repetitions'])

    if command == 'q':
      return False
    elif command == 'a':
      self.n += repetitions
      self.refreshGrid = True
      self.status = 'Measure added'
    elif command == 'd':
      for i in range(repetitions):
        if self.n <= 1: return True
        self.n -= 1
        remove = []
        for onset in self.onsets:
          if grid.measure(onset) == grid.measure(self.pos):
            self.onsets.remove(onset)
          elif grid.measure(onset) > grid.measure(self.pos):
            self.onsets[self.onsets.index(onset)] -= 1
      self.refreshGrid = True
      self.status = 'Measure deleted'
    elif command == 'p':
      try:
        mid = grid.onsets2midi(self.onsets)
        mid.play()
      except Exception:
        return False
    elif command == ' ':
      if self.pos in self.onsets:
        self.onsets.remove(self.pos)
        self.status = 'Note removed'
      else:
        self.onsets.append(self.pos)
        self.status = 'Note added'
      self.refreshGrid = True
    elif command == 'set':
      if match.group(1) == 'numlevels':
        self.numlevels = int(m1.group(2))
        refreshGrid = True
      elif match.group(1) == '':
        pass
    return True

  def annotator(self):
    curses.wrapper(self.graphics)
    return self.beats

  def graphics(self, stdscr):
    #curses.halfdelay(10)
    self.my, self.mx = stdscr.getmaxyx()
    self.height = self.numlevels+2
    self.width = self.mx - 30
    self.posy = int(self.my / 2.0 - self.height / 2.0)
    self.posx = int(self.mx / 2.0 - self.width / 2.0)

    self.metric_grid = curses.newpad(self.height, self.n*grid.beats_per_bar(self.numlevels) + 3)
    com_buffer = curses.newwin(1, self.width, self.posy, self.posx)

    self.buf = ''
    self.exp = re.compile('(?P<repetitions>[0-1]+)?(?P<command1>[adqp ])|:(?P<command2>set) (numlevels) ([0-9]+)')

    while True:
      # Check if the buffer contains a command
      m = self.exp.match(self.buf)
      if m:
        if not self.execute(m):
          break
        self.buf = ''

      self.updateScr(stdscr, self.metric_grid, com_buffer)     
      c = stdscr.getch()
      if c == curses.ERR: continue
      self.status = ''

      if c == 27 or c == curses.KEY_BACKSPACE:
        # Empty buffer
        self.buf = ''
      elif c == curses.KEY_LEFT:
        if self.pos > 0:
          if grid.level(self.pos) != self.level:
            while grid.level(self.pos) != self.level:
              self.pos -= grid.beatlength(self.numlevels)
          else:
            self.pos -= grid.beatlength(self.level)
      elif c == curses.KEY_RIGHT:
        if self.pos + grid.beatlength(self.level) < self.n:
          if grid.level(self.pos) != self.level:
            while grid.level(self.pos) != self.level:
              self.pos += grid.beatlength(self.numlevels)
          else:
            self.pos += grid.beatlength(self.level)
      elif c == curses.KEY_UP:
        if self.level < self.numlevels-1:
          self.level += 1
      elif c == curses.KEY_DOWN:
        if self.level > 0:
          self.level -= 1
      else:
        if c in range(32, 128):
          self.buf += chr(c)

  def realpos(self, measurepos, spacing):
    return int((measurepos+spacing*measurepos)*grid.beats_per_bar(self.numlevels))
    
  def measurepos(self, pos, spacing):
    return int(round(pos / \
        (grid.beats_per_bar(self.numlevels)+spacing*grid.beats_per_bar(self.numlevels))))

  def updateScr(self, stdscr, metric_grid, com_buffer, spacing=1):
    # Refresh screen
    stdscr.clear()
    stdscr.addstr(self.posy+1+self.height, self.posx, 'Position: {0}\tMeasures: {1}\tLevel: {2}\tNotes:{3}'.format(self.pos, self.n, self.level, len(self.onsets)))
    stdscr.addstr(self.posy+3+self.height, self.posx, 'Status: {0}'.format(self.status))
    stdscr.addstr(self.posy+4+self.height, self.posx, 'Onsets: {0}'.format(' '.join([str(onset) for onset in self.onsets])))
    stdscr.addstr(self.posy+5+self.height, self.posx, 'Gridposition: {0}'.format(self.gridpos))
    stdscr.refresh()
    # Refresh metrical grid
    if self.refreshGrid:
      length = self.n * grid.beats_per_bar(self.numlevels)
      self.metric_grid.resize(self.height, length + spacing*length + 3)
      metric_grid.clear()

      for i in range(self.numlevels):
        metric_grid.addstr(i, 0, 'L{0}'.format(i))
      lines = grid.create_grid(self.numlevels, self.n, spacing=spacing)
      for i in range(len(lines)):
        metric_grid.addstr(i, 3, lines[i])
      onsetsline = [' ' for i in range(length + spacing*length)]
      for i in range(len(self.onsets)):
        onsetsline[self.realpos(self.onsets[i], spacing)] = 'X'
      metric_grid.addstr(self.numlevels, 3, ''.join(onsetsline))
      self.refreshGrid = False

    measurelength = self.measurepos(self.width, spacing)
    if self.pos - self.gridpos > measurelength:
      self.gridpos += measurelength / 2 
    elif self.pos - self.gridpos < 0:
      self.gridpos -= measurelength / 2 

    if self.pos >= self.n:
      self.pos = self.n - grid.beatlength(self.level)

    metric_grid.refresh(0, self.realpos(self.gridpos, spacing), self.posy+1, self.posx, self.posy+1+self.height, self.posx+self.width)
    stdscr.move(self.posy+1+self.numlevels, self.posx+self.realpos(self.pos-self.gridpos, spacing)+3)

    # Refresh buffer display
    com_buffer.clear()
    com_buffer.addstr(0, 0, self.buf)
    com_buffer.refresh()
  

