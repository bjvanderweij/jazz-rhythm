# A collection of tools for representing metrical grids
from jazzr.midi import representation
import math

def level(measurepos, numlevels=4, division=2):
  measurepos = measure_pos(measurepos)
  levels = [[] for i in range(numlevels)]
  for l in range(numlevels):
    levels[l] = [beatlength(l) * i for i in range(numlevels)]
    if measurepos > beatlength(l, division=division):
      measurepos -= beatlength(l, division=division)
    if measurepos in levels[l]: return l
  return -1

def beats_per_bar(numlevels, division=2):
  # Calculate the number of beats per measure
  return int(math.pow(2, numlevels-1))

def beatlength(level, division=2):
  return 1/float(math.pow(2, level))

def measure_pos(pos):
  return pos - int(pos)

def measure(pos):
  return int(pos)

def create_grid(numlevels, n, division=2, spacing=0):
  beats = beats_per_bar(numlevels, division=division)
  lines = []
  # For every level:
  for l in range(numlevels):
    lines +=  ['']
    for m in range(n):
      for i in range(beats):
        if level(i * beatlength(numlevels-1, division=division),\
            division=division, numlevels=numlevels) <= l:
          lines[l] += 'o'
        else:
          lines[l] += ' '
        lines[l] += ''.join([' ' for i in range(spacing)])
    print
  return lines
  

def onsets2midi(onsets, bpm=120, pitch=50, velocity=60):
  mid = representation.MidiFile()
  tactus = 2
  #tactuslength = mid.seconds_to_ticks(60/float(bpm))
  tactuslength = mid.quarternotes_to_ticks(1)
  print tactuslength
  onsets = sorted(onsets)
  mid['0'] = representation.Track(mid, 1)
  for i in range(len(onsets)):
    length = tactuslength
    if i + 1< len(onsets):
      length = (onsets[i+1] - onsets[i])*tactuslength
    on = onsets[i]*tactuslength
    off = on+length
    mid['0'].notes.append(representation.Note(on, off, pitch, velocity))
  return mid
