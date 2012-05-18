from midi import *
from midi.MidiOutFile import MidiOutFile
import copy, os, pygame

base_a4 = 440
names = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
class Note:

  def __init__(self, on, off, pitch, onvelocity, offvelocity=0, annotation=None):
    self.on = on
    self.off = off
    self.pitch = pitch
    self.onvelocity = onvelocity
    self.offvelocity = offvelocity
    # Notes can be marked with a tuple (part, measure, voice, note) that allows mappings between notelists and scores or alignments 
    self.annotation = annotation

  def abs_pitch(self):
    return base_a4*pow(2,(self.pitch-57)/12)

  def duration(self):
    return self.off - self.on

  def name(self):
    return '{0}{1}'.format(names[self.pitch % 12], self.pitch // 12)

  def setLength(self, length):
    self.length = length

  def __str__(self):
    return self.info()

  def info(self):
    return "Note: %s, on: %s, off: %s, on velocity: %s, off velocity: %s" % (self.name(), self.on, self.off, self.onvelocity, self.offvelocity)

class NoteList:

  def __init__(self, midifile=None):
    self.notes = []

    # Dirty MIDI administration
    self.key_signature = None
    self.time_signature = (4, 4, 24, 8)
    self.smtp_offset = None
    self.tempo = 500000
    self.division = 480
    self.sequence_names = []

    # If a file is specified, parse it
    if midifile:
      parser = MidiParser(self)
      stream =  MidiInFile.MidiInFile(parser, open(midifile))
      stream.read()

  def splice(self, begin, end):
    new = NoteList()
    new.key_signature = self.key_signature
    new.time_signature= self.time_signature
    new.smtp_offset   = self.smtp_offset
    new.tempo         = self.tempo
    new.division      = self.division
    new.sequence_names= self.sequence_names
    new.notes = self[begin:end]
    return new

  def simplelist(self):
    return [n.pitch for n in self]

  def printinfo(self):
    print "Number of notes:{0}\nKey signature: {1}\nTime signature: {2}\nSmtp offset: {3}\
        \nTempo (microseconds per quarter-note): {4}\nTime division: {5}".format(\
        len(self), self.key_signature, self.time_signature, self.smtp_offset, self.tempo,\
        self.division)

  # Making this iterable doesn't really add any value yet
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


  def insertEvent(self, events, event):
    # Events are primary ordered by time and secundary ordered by pitch
    # No notes yet? Add at beginning
    if len(events) == 0:
      events = [event]
      return events
    # Insert at the right index
    # Loop through events
    for i in range(len(events)):
      # If you find an event that happened at the SAME TIME
      if events[i][0] == event[0]:
        # And its pitch is LOWER
        if events[i][1] < event[1]:
          # Insert BEFORE
          events.insert(i, event)
          return events
      # If you find an event that happened AFTER the current note_on
      elif events[i][0] > event[0]:
        # Insert the note before this event
        events.insert(i, event)
        return events
    # Right place not found? Append
    return events + [event]

  def toEvents(self):
    events = []
    for n in self:
      events = self.insertEvent(events, (n.on, n.pitch, n.onvelocity, 'on'))
      events = self.insertEvent(events, (n.off, n.pitch, n.offvelocity, 'off'))
    return events


  def exportMidi(self, midifile):
    # Do some preprocessing on the notes, converting them to 
    # ordered note on and note off events:
    print "Preprocessing {0} notes".format(len(self))
    events = self.toEvents()

    print "Creating file"
    out = MidiOutFile(midifile)
    out.header(format=0, nTracks=1, division=self.division)
    out.start_of_track()
    out.sequence_name(', '.join(self.sequence_names))
    out.patch_change(3, 1)
    out.tempo(self.tempo)
    if (self.time_signature):
      out.time_signature(self.time_signature[0],\
          self.time_signature[1],\
          self.time_signature[2],\
          self.time_signature[3])
    if self.key_signature:
      out.key_signature(self.key_signature[0],\
                      self.key_signature[1],\
                      self.key_signature[2],\
                      self.key_signature[3])
    if self.smtp_offset:
      out.smtp_offset(self.smtp_offset[0],\
                      self.smtp_offset[1],\
                      self.smtp_offset[2],\
                      self.smtp_offset[3],\
                      self.smtp_offset[4])
    lastTime = 0
    for e in events:
      if e[3] is 'on':
        out.update_time(e[0]-lastTime)
        lastTime = e[0]
        #out.update_time(96)
        out.note_on(0, e[1], e[2])
      else:
        out.update_time(e[0]-lastTime)
        lastTime = e[0]
        #out.update_time(0)
        out.note_off(0, e[1], e[2])

    out.update_time(0)
    out.end_of_track()
    out.eof()
    out.write()

  def __str__(self):
    string = 'NoteList Object:\n'
    for n in self:
      string += str(n) + "\n" 
    return string

  def insert(self, note):
    if len(self) == 0:
      self.notes = [note]
      return
    index = 0
    for n in self:
      if note.on < n.on:
        self.notes.insert(index, note)
        return
      elif note.on == n.on and note.pitch > n.pitch:
        self.notes.insert(index, note)
        return
      index += 1

    self.notes.append(note)

  def remove(self, item):
    self.notes.remove(item)

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


class MidiParser(MidiOutStream.MidiOutStream):

  """
  This class listens to a select few midi events relevant for a simple midifile containing a pianomelody
  """


  def __init__(self, nlist):
    self.nlist = nlist
    self.notes_on = []
    pass

  # Event Listeners
   
  def channel_message(self, message_type, channel, data):
    pass

  def note_on(self, channel=0, pitch=0x40, onvel=0x40):
    self.notes_on.append((self.abs_time(), pitch, onvel))

  def note_off(self, channel=0, pitch=0x40, offvel=0x40):
    for (on, p, onvel) in self.notes_on:
      # Should check if: note_off is later than note_on, note is even in notes_on
      # note appears only once in notes_on
      if pitch == p:
        self.nlist.insert(Note(on, self.abs_time(), pitch, onvel, offvel))
        self.notes_on.remove((on, pitch, onvel))
        break

  def header(self, format=0, nTracks=1, division=96):
    self.nlist.division = division

  def sequence_name(self, text):
    self.nlist.sequence_names += [text]

  def tempo(self, value):
    self.nlist.tempo = value

  def smtp_offset(self, hour, minute, second, frame, framePart):
    self.nlist.smtp_offset = (hour, minute, second, frame, framePart)

  def time_signature(self, nn, dd, cc, bb):
    self.nlist.time_signature = (nn, dd, cc, bb)

  def key_signature(self, sf, mi):
    self.nlist.key_signature = (sf, mi)

  def sequencer_specific(self, data):pass
  def aftertouch(self, channel=0, note=0x40, velocity=0x40):pass
  def continuous_controller(self, channel, controller, value):pass
  def patch_change(self, channel, patch):pass
  def channel_pressure(self, channel, pressure):pass
  def pitch_bend(self, channel, value):pass
  def system_exclusive(self, data):pass
  def song_position_pointer(self, value):pass
  def song_select(self, songNumber):pass
  def tuning_request(self):pass
  def midi_time_code(self, msg_type, values):pass
  def eof(self):pass
  def start_of_track(self, n_track=0):pass
  def end_of_track(self):pass
  def sysex_event(self, data):pass
  def meta_event(self, meta_type, data):pass
  def sequence_number(self, value):pass
  def text(self, text):pass
  def copyright(self, text):pass
  def instrument_name(self, text):pass
  def lyric(self, text):pass
  def marker(self, text):pass
  def cuepoint(self, text):pass
  def midi_ch_prefix(self, channel):pass
  def midi_port(self, value):pass

if __name__ == '__main__':
  notes = NoteList('../MidiFiles/0848-01.mid')
  #import simple_rule
  #simple_rule.higherIsFaster(notes, 30.0)
  from sequencer import Sequencer
  #seq = Sequencer()
  #seq.play(notes)
  notes.exportMidi('exp_outp.mid')

