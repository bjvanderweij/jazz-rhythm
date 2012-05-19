from jazzr.rawmidi import *

class MidiFile(dict):

  def __init__(self, midifile=None):
    # Dirty MIDI administration
    self.key_signature = None
    self.time_signature = (4, 4, 24, 8)
    self.smtp_offset = None
    self.tempo = 500000
    self.division = 480
    self.sequence_names = []
    self.ctrack = -1
    self.format = -1

    # If a file is specified, parse it
    if midifile:
      parser = MidiParser(self)
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
    return sorted([(t.n, t.name) for t in self.values()], key=lambda x: x[0])

  def exportMidi(self, midifile, tracks=None):
    if not tracks:
      tracks = self.values()

    # Do some preprocessing on the notes, converting them to 
    # ordered note on and note off events:
    print "Creating file"
    out = MidiOutFile(midifile)
    out.header(format=1, nTracks=len(tracks)+1, division=self.division)
    out.start_of_track()
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
        out.patch_change(channel, self[track].channels[str(channel)])
      #out.patch_change(3, 1)
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
    string = 'MidiFile Object:\n'
    for n in self:
      string += str(n) + "\n" 
    return string

  def play(self, track=0, block=True):
    # Make a sequencer instance and run it
    mp = MidiPlayer()
    mp.play(self, track)
    pass


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


  def __init__(self, midifile):
    self.midifile = midifile
    self.notes_on = {}
    self.ctrack = -1
    self.mformat = -1
    pass

  # Event Listeners
   
  def channel_message(self, message_type, channel, data):
    pass

  def note_on(self, channel=0, pitch=0x40, onvel=0x40):
    channel+=1
    if not str(channel) in self.midifile[str(self.ctrack)].channels:
      self.midifile[str(self.ctrack)].channels[str(channel)] = 1
    program = self.midifile[str(self.ctrack)].channels[str(channel)]
    note = Note(self.abs_time(), self.abs_time(), pitch, onvel, channel, program)
    if self.ctrack == -1:
      print 'Midiparser: no track currently active.'
      return
    self.midifile[str(self.ctrack)].notes.append(note)
    if not (pitch, channel) in self.notes_on:
      self.notes_on[pitch, channel] = note

  def note_off(self, channel=0, pitch=0x40, offvel=0x40):
    channel+=1
    if (pitch, channel) not in self.notes_on:
#      print 'Midiparser: Note off before note on?'
      return
    note = self.notes_on[pitch, channel]
    note.off = self.abs_time()
    note.offvel = offvel
    #self.midifile[str(self.ctrack)].insert(Note(on, self.abs_time(), pitch, onvel, offvel))
    del self.notes_on[pitch, channel]

  def header(self, format=0, nTracks=1, division=96):
    self.midifile.division = division
    self.mformat = format
    self.midifile.format = format

  def sequence_name(self, text):
    self.midifile[str(self.ctrack)].name = text

  def tempo(self, value):
    self.midifile.tempo = value

  def smtp_offset(self, hour, minute, second, frame, framePart):
    self.midifile.smtp_offset = (hour, minute, second, frame, framePart)

  def time_signature(self, nn, dd, cc, bb):
    self.midifile.time_signature = (nn, dd, cc, bb)

  def key_signature(self, sf, mi):
    self.midifile.key_signature = (sf, mi)

  def sequencer_specific(self, data):pass
  def aftertouch(self, channel=0, note=0x40, velocity=0x40):pass
  def continuous_controller(self, channel, controller, value):pass
  def patch_change(self, channel, patch):
    channel+=1
    patch+=1
    self.midifile[str(self.ctrack)].channels[str(channel)] = patch
  def channel_pressure(self, channel, pressure):pass
  def pitch_bend(self, channel, value):pass
  def system_exclusive(self, data):pass
  def song_position_pointer(self, value):pass
  def song_select(self, songNumber):pass
  def tuning_request(self):pass
  def midi_time_code(self, msg_type, values):pass
  def eof(self):pass
  def start_of_track(self, n_track=0):
    self.midifile[str(n_track)] = Track(self.midifile, n_track)
    self.ctrack = n_track
  def end_of_track(self):
    self.ctrack=-1
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
