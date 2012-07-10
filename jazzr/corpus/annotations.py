from jazzr.midi import representation
from jazzr.tools import commandline
from jazzr.corpus import midi
from jazzr.annotation import Annotation
import os, re, csv, pickle

corpuspath = '/home/bastiaan/Courses/Jazz-Rhythm/Data/corpus/midi/'
annotationspath = '/home/bastiaan/Courses/Jazz-Rhythm/Data/corpus/annotated/'

def getPath(collection):
  path = '{0}{1}/'.format(annotationspath, collection)
  if os.path.exists(path):
    return path
  print path
  return None

def remove(collection, name):
  path = getPath(collection)
  os.system('rm -r {0}'.format(path))

def copy(collection, name, targetcollection, targetname):
  path = getPath(collection)
  targetpath = '{0}{1}/{2}/'.format(annotationspath, targetcollection, targetname)
  os.system('cp -r {0} {1}'.format(path, targetpath))

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

def versions(name, collection='annotations'):
  files = os.listdir(getPath(collection))
  versions = []
  for f in files:
    (n, v, track, singletrack) = parsepath(f)
    if n == name and v not in versions:
      versions.append(v)
  return sorted(versions)

def tracks(name, version, collection='annotations'):
  files = os.listdir(getPath(collection))
  tracks = []
  for f in files:
    (n, v, track, singletrack) = parsepath(f)
    if n == name and v == version and singletrack:
      tracks.append(track)
  return sorted(tracks)

def parts(name, version, track, collection='annotations'):
  path = '{0}{1}-{2}-{3}'.format(getPath(collection), name, version, track)
  files = os.listdir(path)
  parts = []
  exp = re.compile('annotations-([0-9]+).csv'.format(name))
  for f in files:
    m = exp.match(os.path.basename(f))
    if m:
      if not int(m.group(1)) in parts:
        parts.append(int(m.group(1)))
  return sorted(parts)

def parses(name, version, track, collection='annotations'):
  path = '{0}{1}-{2}-{3}'.format(getPath(collection), name, version, track)
  files = os.listdir(path)
  parts = []
  exp = re.compile('{0}-{1}-{2}-([0-9]+)-parse.pickle'.format(name, version, track))
  for f in files:
    m = exp.match(os.path.basename(f))
    if m:
      if not int(m.group(1)) in parts:
        parts.append(int(m.group(1)))
  return sorted(parts)

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

def exists(collection, name):
  return getPath(collection) != None

def save_parse(collection, name, part, parse):
  path = getPath(collection)
  if not path:
    os.makedirs(path)
  f = open('{0}{1}-parse_{2}'.format(path, name, part), 'wb')
  pickle.dump(annotation, f)

def save(collection, name, metadata, annotations, notes, midifile):
  path = getPath(collection)
  if not path:
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

def load_parse(name, version, track, part, collection='annotations'):
  path = '{0}{1}-{2}-{3}/'.format(getPath(collection), name, version, track)
  f = open('{0}{1}-{2}-{3}-{4}-parse.pickle'.format(path, name, version, track, part), 'rb')
  return pickle.load(f)

def load_midifile(collection, name):
  path = '{0}{1}-{2}-{3}'.format(getPath(collection), name, version, track)
  if not path: return None
  return representation.MidiFile('{0}midi.mid'.format(path))

def load_annotation(name, version, track, part, collection='annotations'):
  path = '{0}{1}-{2}-{3}/'.format(getPath(collection), name, version, track)
  if not path: return None
  propsreader = csv.reader(open('{0}metadata.csv'.format(path), 'rb'))
  propsreader.next()
  notesreader = csv.reader(open('{0}notes.csv'.format(path), 'rb'))
  notesreader.next()

  metadata = {}
  for [key, value] in propsreader:
    if is_number(value):
      metadata[key] = float(value)
    else:
      metadata[key] = value
 
  notes = []
  for [on, off, pitch, velocity] in notesreader:
    notes.append((float(on), float(off), int(pitch), int(velocity)))

  results = []

  annotationreader = csv.reader(open('{0}annotations-{1}.csv'.format(path, part), 'rb'))
  annotationreader.next()
  annotations = []

  for [beat, position, pitch, type] in annotationreader:
    annotations.append((float(beat), int(position), int(pitch), int(type)))

  annotation = Annotation(annotations, notes, metadata)
  annotation.name = '{0}-{1}'.format(annotation.name, part)
  return annotation


def load(collection, name, part=None):
  results = []
  for part in parts(n, v, t):
    results += load_annotation(n, v, t, part)
  return results

def loadAnnotations():
  corpus = []
  for song in songs(): 
    for version in versions(song):
      for track in tracks(song, version):
        corpus += load('annotations', '{0}-{1}-{2}'.format(song, version, track))
  return corpus

def corpus():
  corpus = []
  for song in songs(): 
    for version in versions(song):
      for track in tracks(song, version):
        p = parses(song, version, track)
        for part in parts(song, version, track):
          # Made an error earlier, parses start counting at 1
          if part+1 in p:
            annotation = load_annotation(song, version, track, part)
            parse = load_parse(song, version, track, part+1)
            corpus.append((annotation, parse))
          else:
            name = '{0}-{1}-{2}'.format(song, version, track)
            #print '{0}, part {1} has no analysis!'.format(name, part)
  return corpus
