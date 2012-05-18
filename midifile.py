from midi import *
from midi.MidiOutFile import MidiOutFile
import copy, os, pygame

base_a4 = 440
names = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

class MidiFile:

  def __init__(self, midifile=None):
    self.events = []
    if midifile:
      parser = ParseMidi(self)
      stream =  MidiInFile.MidiInFile(parser, open(midifile))
      stream.read()
      print("{0} midievents parsed".format(len(self.events)))


  def export(self, midifile):
    out = MidiOutFile(midifile)
    for event in self.events:
      getattr(out, event[0])(*event[1:])
    out.write()
  
  def __str__(self):
    for e in self.events:
      print e




class ParseMidi(MidiOutStream.MidiOutStream):

  """
  This class listens to a select few midi events relevant for a simple midifile containing a pianomelody
  """


  def __init__(self, mfile):
    self.mfile = mfile
    pass

  
  # Event Listeners
   
  def channel_message(self, message_type, channel, data):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('channel_message', message_type, channel, data))

  def note_on(self, channel=0, note=0x40, velocity=0x40):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('note_on', channel, note, velocity))

  def note_off(self, channel=0, note=0x40, velocity=0x40):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('note_off', channel, note, velocity))

  def header(self, format=0, nTracks=1, division=96):
    self.mfile.events.append(('header', format, nTracks, division))

  def sequence_name(self, text):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('sequence_name', text))

  def tempo(self, value):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('tempo', value))

  def smtp_offset(self, hour, minute, second, frame, framePart):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('smtp_offset', hour, minute, second, frame, framePart))

  def time_signature(self, nn, dd, cc, bb):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('time_signature', nn, dd, cc, bb))

  def key_signature(self, sf, mi):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('key_signature', sf, mi))

  def sequencer_specific(self, data):
    self.mfile.events.append(('sequencer_specific', data))
  def aftertouch(self, channel=0, note=0x40, velocity=0x40):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('aftertouch', channel, note, velocity))
  def continuous_controller(self, channel, controller, value):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('continuous_controller', channel, controller, value))
  def patch_change(self, channel, patch):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('patch_change', channel, patch))
  def channel_pressure(self, channel, pressure):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('channel_pressure', pressure))
  def pitch_bend(self, channel, value):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('pitch_bend', channel, value))
  def system_exclusive(self, data):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('system_exclusive', data))
  def song_position_pointer(self, value):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('song_position_pointer', value))
  def song_select(self, songNumber):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('song_select', songNumber))
  def tuning_request(self):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('tuning_request'))
  def midi_time_code(self, msg_type, values):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('midi_time_code', msg_type, values))
  def eof(self):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('eof', ))
  def start_of_track(self, n_track=0):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('start_of_track', n_track))
  def end_of_track(self):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('end_of_track', ))
  def sysex_event(self, data):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('sysex_event', data))
  def meta_event(self, meta_type, data):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('meta_event', meta_type, data))
  def sequence_number(self, value):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('sequence_number', value))
  def text(self, text):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('text', text))
  def copyright(self, text):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('copyright', text))
  def instrument_name(self, text):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('instrument_name', text))
  def lyric(self, text):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('lyric', text))
  def marker(self, text):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('marker', text))
  def cuepoint(self, text):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('cuepoint', text))
  def midi_ch_prefix(self, channel):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('midi_ch_prefix', channel))
  def midi_port(self, value):
    self.mfile.events.append(('update_time', self.rel_time()))
    self.mfile.events.append(('midi_port', value))

if __name__ == '__main__':
  roll = PianoRoll('0848-01.mid')
  roll.play()
  import simple_rule
  simple_rule.higherIsFaster(roll, 30.0)
  roll.play()
  roll.exportMidi('exp_outp.mid')

