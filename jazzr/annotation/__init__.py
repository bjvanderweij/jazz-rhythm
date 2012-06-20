"""JazzR

A Library of midi tools and algorithms for analysing rhythm in jazz music
"""

# Some annotation types
NOTE = 0
REST = 1
GRACE = 2
ERROR = 3
END = 4

from jazzr.rhythm import meter
from jazzr.midi import representation
from music21 import *

class Annotation:

  def __init__(annotation, notes, metadata):
    self.annotation = annotation
    self.notes = notes
    self.metadata = metadata
    self.bpm = metadata['bpm']
    self.name = metadata['name']
    self.meter = meter.getMeter(metadata)
    # Onset units per second (1000000 = onsets in microseconds)
    self.scale = 1000000

  def __iter__(self):
    return self.generateItems()

  def __len__(self):
    return len(self.annotation)

  def __contains__(self, annotation):
    for a in self.annotation:
      if a is annotation:
        return True
    return False

  def __getitem__(self, i):
    return self.annotation[i]

  def generateItems(self):
    for a in self.annotation:
      yield a
  
  def position(index):
    """Return the position in in quarternotes of the annotation at the 
    given index."""
    return self[index][0]

  def pitch(index):
    """Return the pitch of the note corresponding to the annotated at 
    the given index."""
    return self[index][2]

  def type(index):
    """Return the type of the annotation at the given index."""
    return self[index][3]

  def onset(index):
    """Return the onset of the note corresponding to the annotation at 
    the given index."""
    return self.notes[self[index][1]]

  def offset(index):
    """Return the offset of the note corresponding to the annotation at 
    the given index."""
    return self.notes[self[index][2]]

  def velocity(index):
    """Return the velocity of the note corresponding to the annotation at 
    the given index."""
    return self.notes[self[index][4]]

  def deviation(index):
    """Calculate the proportion of a beat that the given onset deviates
    from the ideal onset corresponding to the given position."""
    beatlength = self.scale/(self.bpm/60.0)
    beats = self.position(index) / float(self.meter.quarters_per_beat())
    beat_onset = beats * beatlength
    deviation = onset - beat_onset
    return deviation / beatlength

  def onset(index):
    """Calculate the ideal onset of this position given the tempo in metadata"""
    beatlength = self.scale/(self.bpm/60.0)
    beats = self.position(index) / float(self.meter.quarters_per_beat())
    return beats * beatlength

  def bar(index):
    """Return the bar in which this position occurs"""
    beats = self.position(index) / float(self.meter.quarters_per_beat())
    return int(beats // self.meter.beatspb)

  def barposition(index):
    """Calculate the position in quarter notes relative to the 
    beginning of the bar."""
    beats = self.annotation[index] / float(self.meter.quarters_per_beat())
    return beats - self.meter.beatspb * (beats // self.meter.beatspb)

  def quarterLength(index):
    """Return the quarter length of the item at index in annotations."""
    (position, x, pitch, type) = self.annotation[index]
    next = position
    quarterLength = 0
    if type in [NOTE, REST, GRACE]:
      for item in annotation[index+1:]:
        if item[0] != position:
          next = item[0]
          break
      quarterLength = next - position
    return quarterLength

  def realLength(index):
    """Return the length in microseconds that is expected given the bpm..."""
    on = self.annotation[index][0]
    off = on + self.quarterLength(index)  
    return onset(off) - onset(on)

  def split(index):
    """Split notes and rests that span across multiple bars in separate
    (bound) notes and rests."""
    (position, x, pitch, type) = self.annotation[index]
    if not type in [REST, NOTE]:
      return [(position, index, pitch, type)]
    ql = self.quarterLength(index)
    current = position
    remainder = ql
    result = []
    barlength = self.meter.quarters_per_bar()
    while self.bar(current) != self.bar(current + remainder):
      diff = (self.bar(current)+1)*barlength - current
      result.append((current, index, pitch, type))
      remainder -= diff
      current += diff
    if remainder > 0:
      result.append((current, index, pitch, type))
    return result

  def midi2name(pitch):
    return representation.Note(0, 0, pitch, 0).name()

  def transcribe():
    """Return a music21 score object, generated from the annotations"""
    score = stream.Score()
    part = stream.Part()
    measurecount = self.bar(annotation[-1][0])
    if measurecount == 0: return
    for i in range(int(measurecount)):
      part.insert(stream.Measure())
    part[0].insert(0, clef.TrebleClef())
    part[0].insert(0, tempo.MetronomeMark(metadata['bpm']))
    part[0].insert(0, meter.TimeSignature('{0}/{1}'.format(int(metadata['beatspb']), int(metadata['beatdiv']))))
    if 'key' in metadata:
      part[0].insert(0, key.KeySignature(metadata['key']))

    barsplit = []
    for i in range(len(annotation)):
      barsplit += self.split(i)

    temp = self.annotation
    self.annotation = barsplit

    for i in range(len(self)):
      (position, index, pitch, type) = self[i]
      measure = self.bar(position)
      measurepos = self.barposition(position)

      if type in [NOTE, REST, GRACE]:
        quarterLength = self.quarterLength(i)
        if quarterLength < 0: continue
        n = note.Note()
        n.midi = pitch + transpose
        n.duration = duration.Duration(quarterLength)
        if type == GRACE:
          n = n.getGrace()
        if type == REST:
          n = note.Rest(quarterLength)
        part[measure].insert(measurepos, n)

    score.insert(part)
    self.annotation = temp
    return score
