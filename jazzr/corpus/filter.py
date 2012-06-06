from jazzr.corpus import files
from jazzr.midi import representation
import os

def expandchannels(mfiles, outputdir):
  for f in mfiles:
    print 'Loading {0}'.format(f)
    mf = representation.MidiFile(f)
    if not mf: continue
    if not mf.format == 0:
      os.system('cp {0} {1}'.format(f, outputdir))
      continue
    newfile = mf['0'].channels2tracks()
    (name, version, track, singletrack) = files.parsename(mf.name)
    print 'Calling exportMidi("{0}")'.format('{0}{1}'.format(outputdir, files.generatefilename(name, version)))
    newfile.exportMidi('{0}{1}'.format(outputdir, files.generatefilename(name, version)))

def filter(mfiles, durations_thr=20, velocities_thr=10, notes_thr=20, polyphony_lim=2):
  tracks = []
  counter = 0
  for f in mfiles:
    counter += 1
    print '({0}/{1}) loading {2}... '.format(counter, len(mfiles), f),
    mf = representation.MidiFile(f)
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
      events = track.toEvents()
      for event in events:
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

def filtertracks(inputdir, outputdir):
  tracks = filter(files.paths(inputdir))
  import os
  if not os.path.exists(outputdir):
    os.mkdir(outputdir)
  
  for track in tracks:
    (name, version, t, singletrack) = files.parsename(track.midifile.name)
    f = '{0}{1}'.format(outputdir, files.generatefilename(name, version, track.n, True))
    print 'saving {0}'.format(f)
    track.save(f)

