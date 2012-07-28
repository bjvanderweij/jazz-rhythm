from jazzr.rhythm import meter
from jazzr.annotation import Annotation
from jazzr.midi import player, representation, generator
from jazzr.tools import cgui, rbsearch, Fraction
from jazzr.corpus import annotations as annotationcorpus
from jazzr.corpus import midi

import curses, re, math

class Tool:

  ANNOTATING = 0
  PLAYING = 1
  INSERT = 2
  names = {'c':0, 'd':2, 'e':4, 'f':5, 'g':7, 'a':9, 'b':11}

  insertmode = 'Available commands:\n' +\
      '\t<Spacebar>\tInsert note\n'+\
      '\tr\tInsert rest\n' + \
      '\te\tInsert end marker\n' + \
      '\tg\tInsert grace note\n' + \
      '\ts\tSkip current note and mark as playing error\n' +\
      '\tt<division>\tInsert a triplet with total duration 1/<division>'
  annotationmode = 'Available commands:\n' +\
      '\t:<COMMAND> <ARG1> <ARG2>\n'+\
      '\tset\t<correction|beatspb|beatdiv>\n' + \
      '\tplay\tInsert end marker\n' + \
      '\tq quit\tInsert grace note\n' + \
      '\tscore\tSkip current note and mark as playing error' + \
      '\tload\t\n'

  def __init__(self, midifile, annotation=None):
    self.cursor = 0
    self.notepos = 0
    self.midipos = 0
    self.padpos = 0
    self.resolution = 1/16.0
    self.lastpos = 0
    self.midifile = midifile
    self.meter = meter.Meter(self.midifile.time_signature[0], self.midifile.time_signature[1])
    self.bpm = midifile.bpm()
    self.offset = 0
    self.extra = 0

    self.name = self.midifile.name

    self.annotations = []
    self.notelist = []
    self.refreshMidi = True
    self.refreshAnnotation = True
    self.status = ''
    self.mode = self.ANNOTATING
    self.viewcorrection = 0
    self.seq = player.Sequencer()

  def setresolution(self, resolution):
    if not 1/resolution in [math.pow(2, i) for i in range(0, 12)]:
      return False
    self.resolution = resolution
    return True

  def quarters2units(self, quarters):
    return int((quarters/4.0)/self.resolution)

  def units2quarters(self, units):
    return (units*self.resolution) * 4.0

  def notelength2quarters(self, notelength):
    return notelength / (1/4.0)

  def notelength2units(self, notelength):
    return self.quarters2units(self.notelength2quarters(notelength))

  def onset2quarters(self, onset):
    return self.bpm * (onset/60000000.0)

  def onset2units(self, onset):
    return self.quarters2units(self.onset2quarters(onset))

  def midipitch(self, name, octave, sign):
    addition = 0
    if sign:
      if sign == 'b':
        addition = -1
      else:
        addition = 1
    return int(octave) * 12 + self.names[name] + addition

  def pitchname(self, pitch):
    m = re.match('(?P<note>[A-G])(?P<sign>b)?(?P<octave>[0-8])$', representation.Note(0, 0, pitch+self.viewcorrection, 0).name())
    props = m.groupdict()
    if not props['sign']:
      name = '{0} {1}'.format(props['note'], props['octave'])
    else:
      name = '{0}{1}{2}'.format(props['note'], props['sign'], props['octave'])
    return name

  def subtract_annotation(self):
    """Remove all annotated notes from the midifile"""
    pass

  def strip(self):
    """Strip off the silence before the first note"""
    self.midifile.nonemptytrack().strip()
    self.refreshMidi = True

  def load(self, collection=None, name=None):
    if not collection:
      collection = annotationcorpus.collections()[\
          cgui.menu(self.stdscr, 'Choose collection', annotationcorpus.collections())]
    results = annotationcorpus.load(collection, name)
    if results:
      self.annotations = []
      self.midifile = annotationcorpus.load_midifile(collection, name)
      for result in results:
        self.annotations += result.annotation

      metadata = results[0].metadata
      self.notelist = results[0].notes
      self.bpm = metadata['bpm']
      self.offset = metadata['offset']
      self.name = metadata['name']
      self.meter = meter.Meter(metadata['beatspb'], metadata['beatdiv'])
      self.refreshAnnotation = True
      self.refreshMidi = True
      return True
    return False

  def save(self, collection=None, name=None, force=False):
    """Save the annotation to the corpus"""
    if not collection:
      choice = cgui.menu(self.stdscr, 'Collection', annotationcorpus.collections() + ['Add new collection'])
      if choice == -1: return
      elif choice == len(annotationcorpus.collections()):
        collection = cgui.prompt(self.stdscr, 'Collection?')
      else: collection = annotationcorpus.collections()[choice]
    
    if not name:
      name = self.name
    metadata = {'beatdiv':self.meter.beatdiv, 'beatspb':self.meter.beatspb, 'offset':self.offset, 'bpm':self.bpm, 'name':self.name}
    if annotationcorpus.exists(collection, name) and not force:
      if cgui.menu(self.stdscr, 'Item exists, overwrite?', ['No', 'Yes']) != 1: return
    annotationcorpus.save(collection, name, metadata, sorted(self.annotations, key=lambda x: x[0]), self.notelist, self.midifile)

  def addNote(self, pitch=0, type=0, position=-1):
    if not pitch and type in [Annotation.NOTE, Annotation.GRACE, Annotation.ERROR, Annotation.SWUNG]:
      pitch = self.notelist[self.midipos][2]
    if position == -1:
      position = self.units2quarters(self.cursor)
    if type == Annotation.SWUNG and position - int(position) == 0.5:
      position = int(position) + 2/3.0
    self.annotations.append((position, self.midipos, pitch, type))
    self.save(collection='autosave', name='autosave', force=True)

  def execute(self, match):
    props = match.groupdict()
    if self.mode == self.INSERT:
      self.refreshAnnotation = True
      if props['command'] == ' ' or props['command'] == 'r':
        for (quarters, midipos, pitch, type) in self.annotations:
          if self.cursor == self.quarters2units(quarters) and not type in [Annotation.GRACE, Annotation.ERROR]:
            index = self.annotations.index((quarters, midipos, pitch, type))
            del self.annotations[index]
            self.midipos = midipos
            if props['command'] == ' ':
              return True
            else: break
      if props['command'] == ' ':
        self.addNote()
        self.midipos += 1
        self.seq.control(self.seq.STOP, None)
        self.seq.control(self.seq.SETEVENTS, self.midifile.nonemptytrack().toEvents(self.midipos-1, self.midipos))
        self.seq.control(self.seq.PLAY, True)
      elif props['command'] == 'r':
        # Add rest
        self.addNote(type=Annotation.REST)
      elif props['command'] == 'g':
        # Add gracenote
        self.addNote(type=Annotation.GRACE)
        self.midipos += 1
      elif props['command'] == 'e':
        # Add end marker
        self.addNote(type=Annotation.END)
      elif props['command'] == 'w':
        # Add end marker
        self.addNote(type=Annotation.SWUNG)
        self.midipos += 1
      elif props['command'] == 's':
        # Skip and mark as error
        self.addNote(type=Annotation.ERROR)
        self.midipos += 1
      elif re.match('t[0-9]+$', props['command']):
        # Add a triplet
        division = int(props['arg'])
        if not division: 
          cgui.alert(self.stdscr, 'Enter a beatdivision: t<beatdivision>', block=True)
          return True
        allowed = [math.pow(2, p) for p in range(int(math.log(1/float(self.resolution))/math.log(2)-1))]
        if not division in allowed:
            cgui.alert(self.stdscr, 'Beatdivision {0} is invalid.\n'.format(division) +\
                'Either the resolution doesn\'t allow it (try :set resolution <division>)\n' +\
                'or it\'s not a power of two.\n' +\
                'allowed divisions: {0}'.format(allowed), block=True)
            return True
        pattern = cgui.prompt(self.stdscr, 'Enter notes for a triplet with duration 1/{0}'.format(division), length=3)
        exp = re.compile('([ nr])([ nr])([ nr])$')
        m = exp.match(pattern)
        if m:
          self.refreshAnnotation = True
          for g in range(3):
            position = self.units2quarters(self.cursor) + self.notelength2quarters(g*(1/float(division))/3.0)
            if m.group(g+1) == 'n':
              self.addNote(position=position)
              self.midipos += 1
            elif m.group(g+1) == 'r':
              self.addNote(type=Annotation.REST, position=position)
            elif m.group(g+1) == ' ':
              pass
          self.cursor += self.notelength2units(1/float(division))
        else:
          cgui.alert(self.stdscr, 'Couldn\'t parse input.', block=True)
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
        if self.mode == self.PLAYING:
          self.seq.control(self.seq.STOP, None)
          self.seq.control(self.seq.LOADFILE, self.midifile)
          self.seq.control(self.seq.SETEVENTS, self.midifile.nonemptytrack().toEvents(self.midipos))
          self.seq.control(self.seq.PLAY, True)
        elif self.mode == self.ANNOTATING:
          mid = generator.annotations2midi([(quarters, pitch, type) for (quarters, midipos, pitch, type) in self.annotations], meter=self.meter, bpm=self.bpm)
          if mid.nonemptytrack():
            self.seq.control(self.seq.STOP, None)
            self.seq.control(self.seq.LOADFILE, mid)
            self.seq.control(self.seq.SETEVENTS, mid.nonemptytrack().toEvents(self.notepos))
            self.seq.control(self.seq.PLAY, True)
        self.status = 'Playing'
      elif props['action'] == 's':
        self.seq.control(self.seq.STOP, None)
      elif props['action'] == 'x' and self.mode == self.ANNOTATING:
        if len(self.annotations) > 0:
          del self.annotations[self.notepos]
          self.refreshAnnotation = True
      elif props['action'] == 's' and self.mode == self.PLAYING:
        pass
    else:
      if props['command'] == 'set ':
        if props['arg1'] == 'correction':
          self.viewcorrection = int(props['arg2'])
          self.refreshMidi = True
          self.status = 'Transposing {0} semitone(s)'.format(props['arg2'])
        elif props['arg1'] == 'beatdiv':
          self.meter.beatdiv = int(props['arg2'])
          self.refreshAnnotation = True
          self.status = 'Changed beatdivision'
        elif props['arg1'] == 'beatsperbar':
          self.meter.beatspb = int(props['arg2'])
          self.refreshAnnotation = True
          self.status = 'Changed beats per bar'
        elif props['arg1'] == 'resolution':
          if not self.setresolution(1/float(props['arg2'])):
            cgui.alert(self.stdscr, 'Invalid resolution.')
          self.refreshMidi = True
          self.refreshAnnotation = True
      elif props['command'] == 'restore':
        if cgui.menu(self.stdscr, 'Restore last session?', ['No', 'Yes']) == 1:
          if not self.load('autosave', 'lastsession'):
            cgui.alert(self.stdscr, 'No session found')
      elif props['command'] == 'save':
        self.save()
      elif props['command'] == 'strip':
        self.strip()
      elif props['command'] == 'subtract':
        self.subtract()
      elif props['command'] == 'score':
        (name, version, track, singletrack) = midi.parsename(self.name)
        index = rbsearch.load_file()
        hits = rbsearch.find(index, name.replace('_', ' '))
        if len(hits) > 0:
          (song, book) = rbsearch.choose_book(index, hits, stdscr=self.stdscr)
          rbsearch.view(song, book)
      elif props['command'] == 'load':
        if not self.load(name=self.name):

          cgui.alert(self.stdscr, 'No annotations found!')
      elif props['command'] == 'q':
        return False
    return True

  def annotator(self):
    # Initialise sequencer
    self.seq.start()
    self.seq.control(self.seq.LOADFILE, self.midifile)
    self.seq.control(self.seq.LOADTRACK, 1)
    self.seq.control(self.seq.SETOUTPUT, 0)
    # Start gui
    try:
      curses.wrapper(self.graphics)
      if annotationcorpus.exists('autosave', 'autosave'):
        annotationcorpus.remove('autosave', 'autosave')
        self.save('autosave', 'lastsession', force=True)
    finally:
      # Make sure to stop the sequencer 
      self.seq.control(self.seq.QUIT, None)

  def curs_left(self): 
    if self.mode == self.INSERT and self.cursor > 0:
      self.cursor -= 1
      for (quarters, midipos, pitch, type) in self.annotations:
        if self.quarters2units(quarters) == self.cursor:
          self.midipos = midipos
    elif self.mode == self.PLAYING and self.midipos > 0: 
      self.midipos -= 1
    elif self.mode == self.ANNOTATING and self.notepos > 0: 
      self.notepos -= 1
      self.midipos = self.annotations[self.notepos][1]
      self.cursor = self.quarters2units(self.annotations[self.notepos][0])

  def curs_right(self):
    if self.mode == self.INSERT:
      self.cursor += 1
      if self.cursor >= self.length + self.extra:
        self.extra += self.quarters2units(self.meter.quarters_per_bar())
        self.refreshAnnotation = True
      for (quarters, midipos, pitch, type) in self.annotations:
        if self.quarters2units(quarters) == self.cursor:
          self.midipos = midipos
    elif self.mode == self.PLAYING and self.midipos+1 < len(self.notelist): 
      self.midipos += 1
    elif self.mode == self.ANNOTATING and self.notepos+1 < len(self.annotations): 
      self.notepos += 1
      self.midipos = self.annotations[self.notepos][1]
      self.cursor = self.quarters2units(self.annotations[self.notepos][0])

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
    self.stdscr.refresh()

    if annotationcorpus.exists('autosave', 'autosave'):
      if cgui.menu(self.stdscr, 'Annotator quit unexpectedly. Restore last session?', ['Yes', 'No']) == 0:
        self.load('autosave', 'autosave')

    while True:
      exp = re.compile(r'(?P<repetitions>[0-9]+)?(?P<action>[iqpsx ])$|:(?P<command>set |play|stop|pause|save|strip|subtract|q|load|score|restore)(?P<arg1>resolution|correction|beatsperbar|beatdiv)?(?P<arg2> (-)?[0-9]+)?\n$')
      if self.mode == self.INSERT:
        exp = re.compile(r'(?P<command>[ wsrge]|t(?P<arg>[0-9]+))$') 
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
    # Fix some stuff that may have gone out of bounds
    if self.notepos >= len(self.annotations):
      self.notepos = len(self.annotations) - 1
    if self.midipos >= len(self.notelist):
      self.midipos = len(self.notelist) - 1

    # Resize the pads, generate the notelist
    self.annotations = sorted(self.annotations, key=lambda x: x[0])
    alength = 0
    if len(self.annotations) > 0:
      alength = self.quarters2units(self.annotations[-1][0]) + 1
      self.extra = 0
        
    if self.refreshMidi:
      self.notelist = self.generate_notelist()
      self.length = max(self.onset2units(self.notelist[-1][0]) + 1, alength)
      self.midipad.resize(self.height, self.length)
      self.midipad.clear()
    if self.refreshAnnotation:
      if not self.notelist:
        self.notelist = self.generate_notelist()
      self.length = max(self.onset2units(self.notelist[-1][0]) + 1, alength)
      self.annotationpad.resize(self.height, self.length + self.extra + 1)
      self.annotationpad.clear()
     
    # Draw the notes in the midifile and annotation
    for line in range(3):
      if self.refreshMidi:
        for (on, off, pitch, velocity) in self.notelist:
          self.midipad.addstr(line, self.onset2units(on), self.pitchname(pitch)[line])
      if self.refreshAnnotation:
        for (quarters, midipos, pitch, type) in self.annotations:
          cursor = self.quarters2units(quarters)
          if type == Annotation.REST:
            self.annotationpad.addstr(line+1, cursor, 'RES'[line])
          elif type == Annotation.END:
            self.annotationpad.addstr(line+1, cursor, 'END'[line])
          else:
            self.annotationpad.addstr(line+1, cursor, self.pitchname(pitch)[line])
    
    # Draw the ruler
    if self.refreshAnnotation:
      bars = 0
      beats = 0
      for i in range(self.length + self.extra):
        beat = (self.units2quarters(i) / self.meter.quarters_per_beat())
        bar = beat // self.meter.beatspb
        if int(bar) > int(bars):
          self.annotationpad.addstr(0, i, '|')
        elif int(beat) > beats:
          self.annotationpad.addstr(0, i, '.')
        bars = bar
        beats = beat

    self.refreshMidi = False
    self.refreshAnnotation = False

    # Highlight the current note in the midifile 
    (on, off, pitch, velocity) = self.notelist[self.midipos]
    currentpos = self.onset2units(on)
    currentname = self.pitchname(pitch)
    (on, off, pitch, velocity) = self.notelist[self.lastpos]
    lastpos = self.onset2units(on)
    lastname = self.pitchname(pitch)
    for line in range(3):
      self.midipad.addstr(line, lastpos, lastname[line])
      self.midipad.addstr(line, currentpos, currentname[line], curses.A_STANDOUT)
    self.lastpos = self.midipos

    # Set the cursor position and pad position
    xoffset = 0
    yoffset = self.height + 1
    if self.mode == self.ANNOTATING and len(self.annotations) > 0:
      xoffset = self.quarters2units(self.annotations[self.notepos][0])
    elif self.mode == self.INSERT:
      xoffset = self.cursor
    elif self.mode == self.PLAYING:
      xoffset = self.onset2units(self.notelist[self.midipos][0])
      yoffset = 1
    if xoffset - self.padpos > self.width:
      self.padpos = xoffset - self.width / 3
    elif xoffset - self.padpos < 0:
      self.padpos = max(xoffset - self.width / 3, 0)
    self.padpos = int(self.padpos)
    xoffset = int(xoffset)


    # Refresh buffer display
    self.com_buffer.clear()
    self.com_buffer.addstr(0, 0, 'Command >{0}'.format(self.buf.replace('\n', '')))

    # Refresh screen
    self.stdscr.clear()
    modes = ['ANNOTATING', 'PLAYING', 'INSERT']
    types = ['NOTE', 'REST', 'GRACE', 'ERROR', 'END', 'SWUNG']
    beatpos = self.units2quarters(self.cursor) / self.meter.quarters_per_beat()
    self.stdscr.addstr(self.posy+2+2*self.height, self.posx, 'Cursor: {0}\tAnnotation: {1}\tNotes:{2}'.format(self.cursor, self.notepos, self.midipos))
    self.stdscr.addstr(self.posy+3+2*self.height, self.posx, 'Beats: {0}\tBar: {1}'.format(beatpos, beatpos // self.meter.beatspb))
    self.stdscr.addstr(self.posy+4+2*self.height, self.posx, 'Mode: {0}'.format(modes[self.mode]))
    self.stdscr.addstr(self.posy+5+2*self.height, self.posx, 'Status: {0}'.format(self.status))
    self.stdscr.addstr(self.posy+6+2*self.height, self.posx, 'Time signature: {0}/{1}'.format(self.meter.beatspb, self.meter.beatdiv))
    self.stdscr.addstr(self.posy+7+2*self.height, self.posx, 'Midifile bpm: {0}'.format(self.midifile.bpm()))
    if self.mode == self.ANNOTATING:
      if len(self.annotations) > 0:
        self.stdscr.addstr(self.posy+8+2*self.height, self.posx,\
            'Annotation: [Position (quarter notes): {0}, Pointer: {1}, Pitch: {2}, Type: {3}]'.format(\
            self.annotations[self.notepos][0], self.annotations[self.notepos][1],\
            self.pitchname(self.annotations[self.notepos][2]),\
            types[self.annotations[self.notepos][3]]))
    elif self.mode == self.PLAYING or self.mode == self.INSERT:
      if len(self.notelist) > 0:
        self.stdscr.addstr(self.posy+8+2*self.height, self.posx,\
            'Note: [On: {0}, Off: {1}, Pitch: {2}, Velocity: {3}]'.format(\
            self.notelist[self.midipos][0], self.notelist[self.midipos][1],\
            self.pitchname(self.notelist[self.midipos][2]),\
            self.notelist[self.midipos][3]))
    self.stdscr.addstr(self.posy+9+2*self.height, self.posx, 'Name: {0}'.format(self.name))

    # Refresh everything in the right order
    self.stdscr.refresh()
    # Refresh the pads, move the cursor
    self.midipad.refresh(       0, self.padpos, self.posy+1, self.posx, self.posy+1+self.height, self.posx+self.width)
    self.annotationpad.refresh( 0, self.padpos, self.posy+self.height+1, self.posx, self.posy+1+2*self.height, self.posx+self.width)
    self.stdscr.move(self.posy+yoffset, self.posx+xoffset-self.padpos)
    self.com_buffer.refresh()

  def generate_notelist(self):
    notelist = []
    for note in self.midifile.nonemptytrack():
      notelist.append((self.midifile.ticks_to_microseconds(note.on),\
          self.midifile.ticks_to_microseconds(note.off),\
          note.pitch, note.onvelocity))
    return notelist
