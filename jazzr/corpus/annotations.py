from jazzr.midi import representation
from jazzr.tools import commandline
from jazzr.corpus import midi
import os, re, csv

corpuspath = '/home/bastiaan/Courses/Jazz-Rhythm/Data/corpus/midi/'
annotationspath = '/home/bastiaan/Courses/Jazz-Rhythm/Data/corpus/annotated/'

def exists(collection, name):
  path = '{0}{1}/{2}/'.format(annotationspath, collection, name)
  return os.path.exists(path)

def remove(collection, name):
  path = '{0}{1}/{2}/'.format(annotationspath, collection, name)
  os.system('rm -r {0}'.format(path))

def copy(collection, name, targetcollection, targetname):
  path = '{0}{1}/{2}/'.format(annotationspath, collection, name)
  targetpath = '{0}{1}/{2}/'.format(annotationspath, targetcollection, targetname)
  os.system('cp -r {0} {1}'.format(path, targetpath))

def save(collection, name, metadata, annotations, notes, midifile):
  path = '{0}{1}/{2}/'.format(annotationspath, collection, name)
  if not os.path.exists(path):
    os.makedirs(path)
  propswriter = csv.writer(open('{0}metadata.csv'.format(path), 'wb'))
  annotationwriter = csv.writer(open('{0}annotations.csv'.format(path), 'wb'))
  noteswriter = csv.writer(open('{0}notes.csv'.format(path), 'wb'))

  midifile.exportMidi('{0}midi.mid'.format(path))

  propswriter.writerow(['Property', 'Value'])
  for key, value in metadata.iteritems():
    propswriter.writerow([key, value])

  annotationwriter.writerow(['Beat', 'Position', 'Pitch', 'Type'])
  for annotation in annotations:
    annotationwriter.writerow(annotation[:])

  noteswriter.writerow(['On', 'Off', 'Pitch', 'Velocity'])
  for note in notes:
    noteswriter.writerow(note[:])

def collections(path=annotationspath):
  return midi.collections(path=path)

def songs(collection='annotated', path=annotationspath):
  return midi.songs(collection=collection, path=path)

def versions(name, collection='annotated', path=annotationspath):
  return midi.versions(name, collection=collection, path=path)

def tracks(name, version, collection='annotated', path=annotationspath):
  return midi.tracks(name, version, collection=collection, path=path)

def is_number(s):
  try:
    float(s)
    return True
  except ValueError:
    return False

def load(collection, name):
  path = '{0}{1}/{2}/'.format(annotationspath, collection, name)
  if not os.path.exists(path): return None
  propsreader = csv.reader(open('{0}metadata.csv'.format(path), 'rb'))
  propsreader.next()
  annotationreader = csv.reader(open('{0}annotations.csv'.format(path), 'rb'))
  annotationreader.next()
  notesreader = csv.reader(open('{0}notes.csv'.format(path), 'rb'))
  notesreader.next()

  metadata = {}
  for [key, value] in propsreader:
    if is_number(value):
      metadata[key] = float(value)
    else:
      metadata[key] = value
  
  annotations = []
  for [beat, position, pitch, type] in annotationreader:
    annotations.append((float(beat), int(position), int(pitch), int(type)))

  notes = []
  for [on, off, pitch, velocity] in notesreader:
    notes.append((float(on), float(off), int(pitch), int(velocity)))
  
  midifile = representation.MidiFile('{0}midi.mid'.format(path))
  return (metadata, annotations, notes, midifile)

