from jazzr.midi import representation
from jazzr.tools import commandline
import os, re 

path = '/home/bastiaan/Courses/Thesis/JazzParser/midi/corpus/'

def names():
  files = os.listdir(path)
  names = []
  for f in files:
    m = re.match('(.*)\.mid', f)
    if m:
      names.append(m.group(1))
  return names

def files():
  files = os.listdir(path)
  midifiles = []
  for f in files:
    if re.match('.*\.mid', f):
      midifiles.append(f)

  return midifiles

def loadname(name):
  return loadfile('{0}{1}.mid'.format(path, name))

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

def filter(mfiles, durations_thr=20, velocities_thr=10, notes_thr=20, polyphony_lim=2):
  tracks = []
  counter = 0
  for f in mfiles:
    counter += 1
    print '({0}/{1}) loading {2}... '.format(counter, len(mfiles), f),
    mf = loadfile(f)
    if not mf: continue
    print '* '
    for track in mf.values():
      print '\tTrack #{0}: {1}'.format(track.n, track.name),
      notes = len(track)
      durations = {}
      velocities = {}
      polyphony = 1

      if notes < notes_thr:
        print 'REJECTED (too short)'
        continue

      # Determine variation in note lengths and velocities
      for note in track:
        durations[str(note.duration)] = durations.get(str(note.duration), 0) + 1
        velocities[str(note.onvelocity)] = durations.get(str(note.onvelocity), 0) + 1

      # Determine polyphony
      # event = (abs_time, pitch, velocity, type, channel, note_object)
      on = {}
      for event in track.events:
        if event[3] is 'on':
          if on != {}:
            if len(on) + 1 > polyphony:
              polyphony = len(on) + 1
          on[event[1], event[4]] = event[5]
        else:
          if (event[1], event[4]) in on.keys():
            del on[event[1], event[4]]
    
      # Reject if any of these tests is positive
      tests = (len(durations) < durations_thr,\
          len(velocities) < velocities_thr,\
          polyphony > polyphony_lim)
      if True in tests:
        print 'REJECTED (durations, velocities, polyphony) = {0}'.format(tests)
        continue
      
      print 'ACCEPTED'
      tracks.append(track)

  return tracks



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

