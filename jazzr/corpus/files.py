from jazzr.midi import representation
from jazzr.tools import commandline
import os, re 

corpuspath = '/home/bastiaan/Courses/Jazz-Rhythm/jazzr/data/corpus/original/'

def songs(path=corpuspath):
  files = paths(path)
  songs = []
  for f in files:
    (name, version, track, singletrack) = parsepath(f)
    if not name in songs:
      songs.append(name)
  return songs

def versions(song, path=corpuspath):
  files = paths(path)


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
    return (m2.group(1), m2.group(2), m2.group(3), False)
  else:
    print '[parsename error] Invalid name: {0}'.format(name)
    return None

def parsepath(path):
  return parsename(os.path.basename(path))

def generatename(name, version, track=0, singletrack=False):
  name = name.replace(' ', '_')
  name = name.lower()
  if not singletrack:
    return '{0}-{1}'.format(name, version)
  else:
    return '{0}-{1}-{2}'.format(name, version, track)

def generatefilename(name, version, track=0, singletrack=False):
  return '{0}.mid'.format(generatename(name, version, track, singletrack))

def names():
  files = os.listdir(corpuspath)
  names = []
  for f in files:
    m = re.match('(.*)\.mid', f)
    if m:
      names.append(m.group(1))
  return names

def paths(path=corpuspath):
  files = os.listdir(path)
  midifiles = []
  for f in files:
    if re.match('.*\.mid', f):
      midifiles.append('{0}{1}'.format(path, f))

  return midifiles

def files(path=corpuspath):
  files = os.listdir(path)
  midifiles = []
  for f in files:
    if re.match('.*\.mid', f):
      midifiles.append(f)

  return midifiles

def loadname(name):
  return loadfile('{0}{1}.mid'.format(corpuspath, name))

def loadfile(f):
  try:
    return representation.MidiFile(f)
  except:
    print 'Error loading file'
    raise
    return None

def selectfile():
  n = sorted(names())
  choice = commandline.menu('Choose a file', n)
  if choice == -1:
    return None
  return loadname(n[choice])




# A corpus item consists of one midifile containing a jazz performance
# It contains seperate midifiles for seperate tracks that have been annotated
# It contains python pickles/text/xml files with annotations
# It contains metadata per annotation: song name, instrument name, instrument
# part (bass, melody, percussion, accompaniment)
class CorpusItem:

  def __init__(self, name, song, alignments):
    pass



if __name__ == '__main__':
  tracks = filter(files())
  import os
  if not os.path.exists('output'):
    os.mkdir('output')
  
  for track in tracks:
    name = 'output/{0}-#{1}.mid'.format(track.midifile.name, track.n)
    print 'saving {0}'.format(name)
    track.save(name)
    #track.play()

