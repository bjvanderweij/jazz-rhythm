from jazzr.midi import representation
from jazzr.tools import commandline
from jazzr.corpus import midi
from jazzr.annotation import Annotation
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
  annotationcount = 0
  noteswriter = csv.writer(open('{0}notes.csv'.format(path), 'wb'))

  midifile.exportMidi('{0}midi.mid'.format(path))

  propswriter.writerow(['Property', 'Value'])
  for key, value in metadata.iteritems():
    propswriter.writerow([key, value])

  writing = False 
  for annotation in annotations:
    if not writing:
      annotationwriter = csv.writer(open('{0}annotations-{1}.csv'.format(path, annotationcount), 'wb'))
      annotationwriter.writerow(['Beat', 'Position', 'Pitch', 'Type'])
      writing = True
    annotationwriter.writerow(annotation[:])
    if annotation[3] == Annotation.END:
      annotationcount += 1
      writing = False

  noteswriter.writerow(['On', 'Off', 'Pitch', 'Velocity'])
  for note in notes:
    noteswriter.writerow(note[:])

def collections(path=annotationspath):
  return midi.collections(path=path)

def songs(collection='annotations', path=annotationspath):
  files = os.listdir('{0}{1}/'.format(path, collection))
  names = []
  for f in files:
    (n, v, track, singletrack) = parsepath(f)
    if not n in names:
      names.append(n)
  return sorted(names)

def versions(name, collection='annotations', path=annotationspath):
  files = os.listdir('{0}{1}/'.format(path, collection))
  versions = []
  for f in files:
    (n, v, track, singletrack) = parsepath(f)
    if n == name and v not in versions:
      versions.append(v)
  return sorted(versions)

def tracks(name, version, collection='annotations', path=annotationspath):
  files = os.listdir('{0}{1}/'.format(path, collection))
  tracks = []
  for f in files:
    (n, v, track, singletrack) = parsepath(f)
    if n == name and v == version and singletrack:
      tracks.append(track)
  return sorted(tracks)

def is_number(s):
  try:
    float(s)
    return True
  except ValueError:
    return False

def parsename(name):
  """Return the name version and track number.

  Return a tuple (name, version, track, singletrack) where version and track
  are integers, multitrack is a boolean indicating whether this is a singel 
  track file. If it is not, track is zero, otherwise track indicates the track
  number.
  """
  m1 = re.match('([a-z_]+)-([0-9]+)(\.mid)?$', name)
  m2 = re.match('([a-z_]+)-([0-9]+)-([0-9]+)(\.mid)?$', name)
  if m1:
    return (m1.group(1), m1.group(2), 0, False)
  elif m2:
    return (m2.group(1), m2.group(2), m2.group(3), True)
  else:
    print '[parsename error] Invalid name: {0}'.format(name)
    return None

def parsepath(path):
  return parsename(os.path.basename(path))

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

def loadAll():
  corpus = []
  for song in songs(): 
    for version in versions(song):
      for track in tracks(song, version):
        metadata, annotation, notes, midifile = load('annotations', '{0}-{1}-{2}'.format(song, version, track))
        corpus += [Annotation(annotation, notes, metadata)]
  return corpus
