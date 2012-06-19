from jazzr.rhythm import meter
from jazzr.midi import representation
import jazzr.annotation as types

def deviation(position, onset, metadata):
  """Calculate the proportion of a beat that the given onset deviates
  from the ideal onset corresponding to the given position."""
  # Onset units per second (1000000 = onsets in microseconds)
  scale = 1000000
  m = meter.getMeter(metadata)
  bpm = metadata['bpm']
  beatlength = scale/(bpm/60.0)
  beats = position / float(m.quarters_per_beat())
  beat_onset = beats * beatlength
  deviation = onset - beat_onset
  return deviation / beatlength

def onset(position, metadata):
  """Calculate the ideal onset of this position given the tempo in metadata"""
  scale = 1000000
  m = meter.getMeter(metadata)
  bpm = metadata['bpm']
  beatlength = scale/(bpm/60.0)
  beats = position / float(m.quarters_per_beat())
  return beats * beatlength

def bar(position, metadata):
  """Return the bar in which this position occurs"""
  m = meter.getMeter(metadata)
  beats = position / float(m.quarters_per_beat())
  return int(beats // m.beatspb)

def barposition(position, metadata):
  """Calculate the position in quarter notes relative to the 
  beginning of the bar"""
  m = meter.getMeter(metadata)
  beats = position / float(m.quarters_per_beat())
  return beats - m.beatspb * (beats // m.beatspb)

def quarterLength(annotation, index, metadata):
  """Return the quarter length of the item at index in annotations"""
  (position, index, pitch, type) = annotation[index]
  next = position
  quarterLength = 0
  if type in [types.NOTE, types.REST, types.GRACE]:
    for item in annotation[index+1:]:
      if item[0] != position:
        next = item[0]
        break
    quarterLength = next - position
  return quarterLength

def realLength(annotation, index, metadata):
  on = annotation[index][0]
  off = on + quarterLength(annotation, index, metadata)  
  return onset(off) - onset(on)

def split(annotation, index, metadata):
  (position, x, pitch, type) = annotation[index]
  m = meter.getMeter(metadata)
  if not type in [types.REST, types.NOTE]:
    return [(position, index, pitch, type)]
  ql = quarterLength(annotation, index, metadata)
  current = position
  remainder = ql
  result = []
  barlength = m.quarters_per_bar()
  while bar(current, metadata) != bar(current + remainder, metadata):
    diff = (bar(current, metadata)+1)*barlength - current
    result.append((current, index, pitch, type))
    remainder -= diff
    current += diff
  if remainder > 0:
    result.append((current, index, pitch, type))
  return result

def midi2name(pitch):
  return representation.Note(0, 0, pitch, 0).name()
