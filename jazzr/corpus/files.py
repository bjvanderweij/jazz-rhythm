from jazzr.midi import representation
from jazzr.tools import commandline
import os, re 

corpuspath = '/home/bastiaan/Courses/Jazz-Rhythm/jazzr/data/corpus/'

def collections(path=corpuspath):
  collections = []
  for c in os.listdir(corpuspath):
    if os.path.isdir('{0}{1}'.format(path, c)):
      collections.append(c)
  return sorted(collections)

def songs(collection='original', path=corpuspath):
  files = paths(path, collection=collection)
  names = []
  for f in files:
    (n, v, track, singletrack) = parsepath(f)
    if not n in names:
      names.append(n)
  return sorted(names)

def versions(name, collection='original', path=corpuspath):
  files = paths(path, collection=collection)
  versions = []
  for f in files:
    (n, v, track, singletrack) = parsepath(f)
    if n == name and v not in versions:
      versions.append(v)
  return sorted(versions)

def tracks(name, version, collection='original', path=corpuspath):
  files = paths(path, collection=collection)
  tracks = []
  for f in files:
    (n, v, track, singletrack) = parsepath(f)
    if n == name and v == version and singletrack:
      tracks.append(track)
  return sorted(tracks)

def load(name, version, track, singletrack, collection='original', path=corpuspath):
  f = path + collection + '/' + generatefilename(name, version, track, singletrack)
  return representation.MidiFile(path + collection + '/' + generatefilename(name, version, track, singletrack))

def remove(name, version, track, singletrack, collection='original', path=corpuspath):
  os.remove(path + collection + '/' + generatefilename(name, version, track, singletrack))

def save(name, version, track, singletrack, collection, midifile, path=corpuspath):
  f = path + collection + '/' + generatefilename(name, version, track, singletrack)
  midifile.exportmidi(f)

def copy(name, version, track, singletrack, source, target, path=corpuspath):
  fsource = path + source + '/' + generatefilename(name, version, track, singletrack)
  ftarget = path + target + '/' + generatefilename(name, version, track, singletrack)
  os.system('cp {0} {1}'.format(fsource, ftarget))

def move(name, version, track, singletrack, source, target, path=corpuspath):
  fsource = path + source + '/' + generatefilename(name, version, track, singletrack)
  ftarget = path + target + '/' + generatefilename(name, version, track, singletrack)
  os.system('mv {0} {1}'.format(fsource, ftarget))

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

def generatename(name, version, track=0, singletrack=False):
  name = name.replace(' ', '_')
  name = name.lower()
  if not singletrack:
    return '{0}-{1}'.format(name, version)
  else:
    return '{0}-{1}-{2}'.format(name, version, track)

def generatefilename(name, version, track=0, singletrack=False):
  return '{0}.mid'.format(generatename(name, version, track, singletrack))

def paths(path=corpuspath, collection='original'):
  files = os.listdir('{0}{1}/'.format(path, collection))
  midifiles = []
  for f in files:
    if re.match('.*\.mid', f):
      midifiles.append('{0}{1}/{2}'.format(path, collection, f))
  return midifiles

def files(path=corpuspath, collection='original'):
  files = os.listdir('{0}{1}/'.format(path, collection))
  midifiles = []
  for f in files:
    if re.match('.*\.mid', f):
      midifiles.append(f)

  return midifiles



def selectfile(collection=None, song=None, version=None, track=None):
  level = 1
  midifile = None
  while level > 0 and not midifile:
    if level == 1 and not collection:   
      choice = commandline.menu('Choose collection', collections())
      if choice == -1:
        level -= 1
        continue
      else: level += 1
      collection = collections()[choice]
    elif level == 2 and not song:   
      choice = commandline.menu('Choose song', songs(collection=collection))
      if choice == -1:
        level -= 1
        continue
      else: level += 1
      song = songs(collection=collection)[choice]
    elif level == 3 and not version:   
      choice = commandline.menu('Choose version', versions(song, collection=collection))
      if choice == -1: 
        level -= 1
        continue
      else: level += 1
      version = versions(song, collection=collection)[choice]
    elif level == 4 and not track:   
      singletrack = False
      track = 0
      if len(tracks(song, version, collection=collection)) > 0:
        singletrack = True
        choice = commandline.menu('Choose track', tracks(song, version, collection=collection))
        if choice == -1:
          level -= 1
          continue
        else: level += 1
        track = tracks(song, version, collection=collection)[choice]
    elif level < 4:
      level += 1
    else: 
      return load(song, version, track, singletrack, collection=collection)





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

