from jazzr.rawmidi import *
from jazzr.midi import tools
import copy, os, pygame, threading

class Note:

  def __init__(self, on, off, pitch, onvelocity, offvelocity=0, annotation=None, channel=0, program=None):
    self.base_a4 = 440
    self.names = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
    self.on = on
    self.off = off
    self.pitch = pitch
    self.onvelocity = onvelocity
    self.offvelocity = offvelocity
    # Notes can be marked with a tuple (part, measure, voice, note) that allows mappings between notelists and scores or alignments 
    self.annotation = annotation
    self.channel = channel
    self.program = program

  def instrument(self):
    # Program and channel needs to be +1'ed (something with starting at zero)
    (instr, perc, fam) = tools.prog2instr(self.program+1)
    if not self.isPercussion():
      return instr
    return perc

  def family(self):
    # Program and channel needs to be +1'ed (something with starting at zero)
    (instr, perc, fam) = tools.prog2instr(self.program+1)
    if not self.isPercussion():
      return fam
    return None

  def isPercussion(self):
    # Program and channel needs to be +1'ed (something with starting at zero)
    return self.channel+1 is 10

  def abs_pitch(self):
    return self.base_a4*pow(2,(self.pitch-57)/12)

  def duration(self):
    return self.off - self.on

  def name(self):
    return '{0}{1}'.format(self.names[self.pitch % 12], self.pitch // 12)

  def setLength(self, length):
    self.length = length

  def __str__(self):
    return self.info()

  def info(self):
    return "Note: %s, on: %s, off: %s, on velocity: %s, off velocity: %s" % (self.name(), self.on, self.off, self.onvelocity, self.offvelocity)

class Track:

  def __init__(self, midifile, n=0, annotation=None):
    self.n = n
    self.channels = {}
    self.notes = []
    self.name = ''
    self.midifile = midifile
    self.annotation = annotation

  def __iter__(self):
    return self.generateItems()

  def __len__(self):
    return len(self.notes)

  def __contains__(self, note):
    for n in self.notes:
      if n is note:
        return True
    return False

  def __getitem__(self, i):
    return self.notes[i]

  def generateItems(self):
    for n in self.notes:
      yield n

  def length(self):
    if len(self) == 0: return 0.0
    return self.midifile.ticks_to_microseconds(self[len(self)-1].off)

  def simplelist(self):
    return [n.pitch for n in self]

  def toEvents(self):
    events = []
    for n in self:
      events.append((n.on, n.pitch, n.onvelocity, 'on', n.channel, n.program))
      events.append((n.off, n.pitch, n.offvelocity, 'off', n.channel, n.program))
    return sorted(events, key=lambda x: x[0])

  def save(self, fname):
    """Save this track in a separate midi file."""
    self.midifile.exportMidi(fname, tracks=[str(self.n)])

  def channels2tracks(self):
    """Expand channels into separate tracks and put it in a new midi file."""
    programs = {}
    channels = {}
    tracks = {}
    midifile = self.midifile.newFile()
    midifile.format = 1
    counter = 1
    for n in self:
      if str(n.program) in tracks:
        tracks[str(n.program)].notes.append(n)
      else:
        tracks[str(n.program)] = Track(midifile, counter)
        tracks[str(n.program)].channels[1] = n.program
        tracks[str(n.program)].name = n.instrument()
        counter += 1
    for t in tracks.values():
      midifile[str(t.n)] = t
    return midifile

  def play(self, gui=False, block=True):
    """Try to play this track."""
    self.midifile.play(str(self.n), gui=gui, block=block)

  def remove(self, item):
    """Remove a note from this track."""
    self.notes.remove(item)

class MidiFile(dict):

  def __init__(self, midifile=None):
    from jazzr.midi import parser
    # Dirty MIDI administration
    self.key_signature = None
    self.time_signature = (4, 4, 24, 8)
    self.smtp_offset = None
    self.tempo = 500000
    self.division = 480
    self.sequence_names = []
    self.ctrack = -1
    self.format = 1

    # If a file is specified, parse it
    if midifile:
      parser = parser.MidiParser(self)
      stream =  MidiInFile.MidiInFile(parser, open(midifile))
      stream.read()
      self.name = midifile.split('/')[-1]

  def newFile(self):
    new = MidiFile()
    new.key_signature = self.key_signature
    new.time_signature= self.time_signature
    new.smtp_offset   = self.smtp_offset
    new.tempo         = self.tempo
    new.division      = self.division
    new.name          = self.name
    return new

  def printinfo(self):
    print "Number of tracks:{0}\nKey signature: {1}\nTime signature: {2}\nSmtp offset: {3}\
        \nTempo (microseconds per quarter-note): {4}\nTime division: {5}".format(\
        len(self), self.key_signature, self.time_signature, self.smtp_offset, self.tempo,\
        self.division, '\n'.join('Notes in track {0}: {1}'.format(x, len(self[x])) for x in self))

  def tracknames(self):
    """Return a list of track names sorted by track number."""
    return sorted([(t.n, t.name) for t in self.values()], key=lambda x: x[0])

  def exportMidi(self, midifile, tracks=None):
    """Create a type 1 midi file.

    The name of track 0 will be the midifile name, so the original
    name of track 0 will be lost.
    """
    from jazzr.rawmidi.MidiOutFile import MidiOutFile
    if not tracks:
      tracks = self.keys()

    # Do some preprocessing on the notes, converting them to 
    # ordered note on and note off events:
    out = MidiOutFile(midifile)
    out.header(format=1, nTracks=len(tracks)+1, division=self.division)

    out.start_of_track()
    out.sequence_name(self.name)
    out.tempo(self.tempo)
    if (self.time_signature):
      out.time_signature(self.time_signature[0],\
        self.time_signature[1],\
        self.time_signature[2],\
        self.time_signature[3])
    if self.key_signature:
      out.key_signature(self.key_signature[0],\
        self.key_signature[1])
    if self.smtp_offset:
      out.smtp_offset(self.smtp_offset[0],\
        self.smtp_offset[1],\
        self.smtp_offset[2],\
        self.smtp_offset[3],\
        self.smtp_offset[4])
    out.end_of_track()

    for track in tracks:
      events = self[track].toEvents()
      out.start_of_track()
      out.sequence_name(self[track].name)
      # This is not a neat solution. Channels may change during the track
      for channel in self[track].channels.keys():
        out.patch_change(int(channel), self[track].channels[channel])
      #out.patch_change(3, 1)
      lastTime = 0
      for e in events:
        if e[3] is 'on':
          out.update_time(e[0]-lastTime)
          lastTime = e[0]
          #out.update_time(96)
          out.note_on(e[4], e[1], e[2])
        else:
          out.update_time(e[0]-lastTime)
          lastTime = e[0]
          #out.update_time(0)
          out.note_off(e[4], e[1], e[2])

      out.update_time(0)
      out.end_of_track()
    out.eof()
    out.write()

  def __str__(self):
    string = 'MidiFile Object:\n'
    for n in self:
      string += str(n) + "\n" 
    return string

  def play(self, track=0, block=True, gui=False):
    from jazzr.midi import player
    # Make a sequencer instance and run it
    mp = player.Player()
    mp.play(self, track, gui=gui, block=block)


  def quarternotes_to_ticks(self, quarternotes):
    return self.microseconds_to_ticks(quarternotes * self.tempo)

  def microseconds_to_ticks(self, microseconds):
    return int((microseconds / float(self.tempo)) * self.division)
  
  def milliseconds_to_ticks(self, microseconds):
    return int((0.001 * microseconds / float(self.tempo)) * self.division)
  
  def seconds_to_ticks(self, microseconds):
    return int((0.000001 * microseconds / float(self.tempo)) * self.division)
  
  def ticks_to_quarternotes(self, ticks):
    return self.ticks_to_microseconds(ticks) / self.tempo

  def ticks_to_microseconds(self, ticks):
    return (ticks / float(self.division)) * float(self.tempo)

  def ticks_to_milliseconds(self, ticks):
    return (ticks / float(self.division)) * float(self.tempo) / 1000.0
  
  def ticks_to_seconds(self, ticks):
    return (ticks / float(self.division)) * float(self.tempo) / 1000000.0
  
  def ioi(self, note):
    if note == 0: return 0
    return self.notes[note].on - self.notes[note-1].on

  def duration(self, note):
    return self.notes[note].duration
