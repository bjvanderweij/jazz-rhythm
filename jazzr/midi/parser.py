from jazzr.rawmidi import *
from jazzr.midi import representation

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
    note = representation.Note(self.abs_time(), self.abs_time(), pitch, onvel, channel, program)
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
    self.midifile[str(n_track)] = representation.Track(self.midifile, n_track)
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
