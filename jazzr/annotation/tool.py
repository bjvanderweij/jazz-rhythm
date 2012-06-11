from jazzr.rhythm import grid
from jazzr.midi import player
from jazzr.midi import representation
from jazzr.tools import cgui

import curses, re, math

class Tool:

  ANNOTATING = 0
  PLAYING = 1
  INSERT = 2
  names = {'c':0, 'd':2, 'e':4, 'f':5, 'g':7, 'a':9, 'b':11}
    
  def __init__(self, midifile, beats_per_bar=4, beatdivision=4, annotationfile=None):
    self.cursor = 0
    self.notepos = 0
    self.midipos = 0
    self.padpos = 0
    self.maxdiv = 16
    self.lastpos = 0
    self.midifile = midifile
    self.n = 1
    self.annotation = {}
    # Quarter notes per bar
    self.annotation['beatspb'] = beats_per_bar
    # Division unit of a beat (e.g. 4 means 1/4, 8 means 1/8)
    self.annotation['beatdivision'] = beatdivision
    self.annotation['notes'] = []
    self.notelist = None
    self.refreshMidi = True
    self.refreshAnnotation = True
    self.status = ''
    self.mode = self.ANNOTATING
    self.viewcorrection = 0
    self.seq = player.Sequencer()

  def setmaxdiv(self, maxdiv):
    if not maxdiv in [math.pow(2, i) for i in range(0, 8)]:
      return False
    self.maxdiv = maxdiv
   
  def units_per_quarternote(self):
    return (1/4.0) / (1/float(self.maxdiv))

  def units_per_beat(self):
    return (1/float(self.annotation['beatdivision'])) /\
        (1/float(self.maxdiv))

  def quarters_per_bar(self):
    return self.annotation['beatspb'] * \
        (1/float(self.annotation['beatdivision'])) /\
        (1/4.0)

  def midiscale(self):
    # Number of ticks per unit (specified by maxdiv)
    return self.midifile.quarternotes_to_ticks(1) / self.units_per_quarternote()

  def pos_to_quarternotes(self, pos):
    return pos / self.units_per_quarternote()

  def pos_to_beats(self, pos):
    return pos / self.units_per_beat()

  def midipitch(self, name, octave, sign):
    addition = 0
    if sign:
      if sign == 'b':
        addition = -1
      else:
        addition = 1
    return int(octave) * 12 + self.names[name] + addition

  def subtract_annotation(self):
    """Remove all annotated notes from the midifile"""
    pass

  def strip(self):
    """Strip off the silence before the first note"""
    firstnote = self.midifile
    pass

  def save(self):
    """Save the annotation to the corpus"""
    for n1, n2 in zip(self.annotation['notes'], self.notelist[:len(self.annotation['notes'])]):
      if n1[2] != n2[2]:
        cgui.calert(self.stdscr, 'Not all  notes are annotated', block=True)
        return
    collection = cgui.prompt(self.stdscr, 'Collection?')
    cgui.calert(self.stdscr, collection, block=True)
    name = cgui.prompt(self.stdscr, 'Name?')
    pass    

  def execute(self, match):
    props = match.groupdict()
    if self.mode == self.INSERT:
      self.refreshAnnotation = True
      for note in self.annotation['notes']:
        if note[0] == self.cursor:
          index = self.annotation['notes'].index(note)
          del self.annotation['notes'][index]
          self.midipos = index
          return True
      if not props['note']:
        self.annotation['notes'].append((self.cursor, self.notelist[self.midipos][1], self.notelist[self.midipos][2]))
        self.midipos += 1
        self.seq.control(self.seq.STOP, None)
        self.seq.control(self.seq.SETEVENTS, self.midifile['1'].toEvents(self.midipos-1, self.midipos))
        self.seq.control(self.seq.PLAY, True)
      else:
        pitch = self.midipitch(props['note'].lower(), props['octave'], props['sign'])
        sign = ' '
        if props['sign']:
          sign = props['sign']
        name = '{0}{1}{2}'.format(props['note'].upper(), sign, props['octave'])
        self.annotation['notes'].append((self.cursor, name, pitch))
    elif props['action']:
      if props['action'] == 'q':
        return False
      elif props['action'] == 'i':
        self.mode = self.INSERT
        self.status = 'Entering insert mode'
      elif props['action'] == 'r':
        self.mode = self.INSERT
        self.status = 'Entering insert mode'
      elif props['action'] == 'p':
        self.seq.control(self.seq.STOP, None)
        self.seq.control(self.seq.SETEVENTS, self.midifile['1'].toEvents(self.midipos))
        self.seq.control(self.seq.PLAY, True)
        self.status = 'Playing'
      elif props['action'] == 's':
        self.seq.control(self.seq.STOP, None)
    else:
      if props['command'] == 'set ':
        if props['arg1'] == 'correction':
          self.viewcorrection = int(props['arg2'])
          self.refreshMidi = True
          self.status = 'Transposing {0} semitone(s)'.format(props['arg2'])
        if props['arg1'] == 'beatdivision':
          self.annotation['beatdivision'] = int(props['arg2'])
          self.refreshAnnotation = True
          self.status = 'Changed beatdivision'
        if props['arg1'] == 'beatsperbar':
          self.annotation['beatspb'] = int(props['arg2'])
          self.refreshAnnotation = True
          self.status = 'Changed beats per bar'
      elif props['command'] == 'save':
        self.save()
      elif props['command'] == 'strip':
        self.strip()
      elif props['command'] == 'subtract':
        self.subtract()
      elif props['command'] == 'q':
        return False
    return True

  def annotator(self):
    self.seq.start()
    self.seq.control(self.seq.LOADFILE, self.midifile)
    self.seq.control(self.seq.LOADTRACK, 1)
    self.seq.control(self.seq.SETOUTPUT, 0)
    try:
      curses.wrapper(self.graphics)
    finally:
      self.seq.control(self.seq.QUIT, None)
    return self.annotation

  def curs_left(self): 
    if self.mode == self.INSERT and self.cursor > 0:
      self.cursor -= 1
    elif self.mode == self.PLAYING and self.midipos > 0: 
      self.midipos -= 1
    elif self.mode == self.ANNOTATING and self.notepos > 0: 
      self.notepos -= 1

  def curs_right(self):
    if self.mode == self.INSERT and self.cursor+1 < self.notelist[-1][0]:
      self.cursor += 1
    elif self.mode == self.PLAYING and self.midipos+1 < len(self.notelist): 
      self.midipos += 1
    elif self.mode == self.ANNOTATING and self.notepos+1 < len(self.annotation['notes']): 
      self.notepos += 1

  def graphics(self, stdscr):
    self.stdscr = stdscr
    self.my, self.mx = self.stdscr.getmaxyx()
    self.height = 4
    self.width = self.mx - 30
    self.posy = int(self.my / 2.0 - self.height / 2.0)
    self.posx = int(self.mx / 2.0 - self.width / 2.0)

    self.midipad = curses.newpad(self.height, 1) 
    self.annotationpad = curses.newpad(self.height, 1)
    self.com_buffer = curses.newwin(1, self.width, self.posy, self.posx)

    self.buf = ''

    while True:
      exp = re.compile(r'(?P<repetitions>[0-9]+)?(?P<action>[iqps ])$|:(?P<command>set |play|stop|pause|save|strip|subtract|q)(?P<arg1>correction|beatsperbar|beatdivision)?(?P<arg2> (-)?[0-9]+)?\n$')
      if self.mode == self.INSERT:
        exp = re.compile(r'(?P<note>[a-gA-G])(?P<sign>[#b])?(?P<octave>[1-8]) $| $') 
      # Check if the buffer contains a command
      m = exp.match(self.buf)
      if m:
        if not self.execute(m):
          break
        self.buf = ''

      self.updateScr(self.stdscr)
      c = self.stdscr.getch()
      if c == curses.ERR: continue
      self.status = ''

      if c == 27: # or c == curses.KEY_BACKSPACE:
        if self.mode == self.INSERT:
          self.mode = self.ANNOTATING
          self.status = 'Leaving insert mode'
        # Empty buffer
        self.buf = ''
      elif c == curses.KEY_BACKSPACE:
        # Empty buffer
        self.buf = ''
      elif c == curses.KEY_LEFT:
        self.curs_left()
      elif c == curses.KEY_RIGHT:
        self.curs_right()
      elif c == curses.KEY_UP and self.mode != self.INSERT:
        if self.mode == self.ANNOTATING:
          self.mode = self.PLAYING
      elif c == curses.KEY_DOWN and self.mode != self.INSERT:
        if self.mode == self.PLAYING:
          self.mode = self.ANNOTATING
      else:
        if c in range(32, 128) + [10]:
          self.buf += chr(c)

  def updateScr(self, stdscr):
    # Refresh screen
    self.stdscr.clear()
    modes = ['ANNOTATING', 'PLAYING', 'INSERT']
    beatpos = self.pos_to_beats(self.cursor)
    self.stdscr.addstr(self.posy+2+2*self.height, self.posx, 'Cursor: {0}\tNote position: {1}\tMidifile position:{2}'.format(self.cursor, self.notepos, self.midipos))
    self.stdscr.addstr(self.posy+3+2*self.height, self.posx, 'Beats: {0}\tBar: {1}'.format(beatpos, beatpos // self.annotation['beatspb']))
    self.stdscr.addstr(self.posy+4+2*self.height, self.posx, 'Mode: {0}'.format(modes[self.mode]))
    self.stdscr.addstr(self.posy+5+2*self.height, self.posx, 'Status: {0}'.format(self.status))
    self.stdscr.refresh()

    # Resize the pads, generate the notelist
    if self.refreshMidi:
      self.notelist = self.generate_notelist()
      length = self.notelist[-1][0] + 1
      self.midipad.resize(self.height, length)
      self.midipad.clear()
    if self.refreshAnnotation:
      if not self.notelist:
        self.notelist = self.generate_notelist()
      length = self.notelist[-1][0] + 1
      self.annotationpad.resize(self.height, length)
      self.annotationpad.clear()
     
    # Draw the notes in the midifile and annotation
    for line in range(3):
      if self.refreshMidi:
        for note in self.notelist:
          self.midipad.addstr(line, note[0], note[1][line])
      if self.refreshAnnotation:
        for note in self.annotation['notes']:
          self.annotationpad.addstr(line+1, note[0], note[1][line])
    
    # Draw the ruler
    if self.refreshAnnotation:
      bars = 0
      beats = 0
      for i in range(length):
        if self.pos_to_beats(i) // self.annotation['beatspb'] > bars:
          self.annotationpad.addstr(0, i, '|')
        elif int(self.pos_to_beats(i)) > beats:
          self.annotationpad.addstr(0, i, '.')
        bars = self.pos_to_beats(i) // self.annotation['beatspb']
        beats = int(self.pos_to_beats(i))

    self.refreshMidi = False
    self.refreshAnnotation = False

    # Set the cursor position and pad position
    xoffset = 0
    yoffset = self.height + 1
    if self.mode == self.ANNOTATING:
      if len(self.annotation['notes']) > 0:
        xoffset = self.annotation['notes'][self.notepos][0]
    elif self.mode == self.INSERT:
      xoffset = self.cursor
    elif self.mode == self.PLAYING:
      xoffset = self.notelist[self.midipos][0]
      yoffset = 1
    if xoffset - self.padpos > self.width:
      self.padpos += self.width / 2 
    elif xoffset - self.padpos < 0:
      self.padpos -= self.width / 2 

    # Highlight the current note in the midifile 
    currentnote = self.notelist[self.midipos]
    lastnote = self.notelist[self.lastpos]
    for line in range(3):
      self.midipad.addstr(line, lastnote[0], lastnote[1][line])
      self.midipad.addstr(line, currentnote[0], currentnote[1][line], curses.A_STANDOUT)
    self.lastpos = self.midipos

    # Refresh the pads, move the cursor
    self.midipad.refresh(       0, self.padpos, self.posy+1, self.posx, self.posy+1+self.height, self.posx+self.width)
    self.annotationpad.refresh( 0, self.padpos, self.posy+self.height+1, self.posx, self.posy+1+2*self.height, self.posx+self.width)
    self.stdscr.move(self.posy+yoffset, self.posx+xoffset-self.padpos)

    # Refresh buffer display
    self.com_buffer.clear()
    self.com_buffer.addstr(0, 0, self.buf.replace('\n', ''))
    self.com_buffer.refresh()

  def generate_notelist(self):
    notelist = []
    for note in self.midifile.nonemptytrack():
      m = re.match('(?P<note>[A-G])(?P<sign>b)?(?P<octave>[0-8])$', representation.Note(0, 0, note.pitch+self.viewcorrection, 0).name())
      props = m.groupdict()
      if not props['sign']:
        name = '{0} {1}'.format(props['note'], props['octave'])
      else:
        name = '{0}{1}{2}'.format(props['note'], props['sign'], props['octave'])
      notelist.append((int(note.on / float(self.midiscale())), name, note.pitch))
        
    return notelist
  


