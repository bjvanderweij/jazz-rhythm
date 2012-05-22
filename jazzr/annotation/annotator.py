from jazzr.annotation import data as datamod
from jazzr.corpus import files
from jazzr.tools import commandline
from jazzr.midi import representation
import code

def annotate(path):
  midi = representation.MidiFile(path)
  (name, version, track, singletrack) = files.parsename(midi.name)
  key = '{0}-{1}-{2}'.format(name, version, track)

  parts = ['percussion', 'bass', 'accompaniment', 'melody', None]
  part = None
  choice = -1
  while choice not in [4, 5]:
    # Show options: play file,don't add to corpus
    choice = commandline.menu(key, ['Play file', 'Annotate', 'View info', 'Drop to shell', 'Save and next', 'Skip', 'Abort'])
    if choice == 0:
      midi['1'].play(gui=True)
    elif choice == 1:

      part = parts[commandline.menu('Choose value for \'part\' attribute.', parts)]
    elif choice == 2:
      print 'Name:\t{0}\nPath:\t{1}\nInstrument:\t{2}\n'.format(\
        midi.name, path, midi['1'][0].instrument())
    elif choice == 3:
      code.interact(local=locals())
    elif choice == 6:
      if raw_input('Are you sure? (y/n) ') is 'y':
        exit(0)
  if choice == 4:
    return (key, {'path':path, 'part':part})
  if choice == 5:
    return None
      
    


# This function assumes an inputdir containing single track midifiles
# The revise option toggles whether this will iterate over every file in 
# inputdir or just the ones already in the datafile

# Some possibilities should include annotate everything that is [in inputdir], [in datafile AND inputdir]
# [in datafile], [in datafile but missing attribs], etc.
def simpleAnnotator(inputdir, datafile, revise=False, annotatefunction=annotate, saveEach=True):
  data = datamod.Data(datafile)
  if revise and 'path' in d.keys:
    paths = [item['path'] for item in data.values()]
  aset = files.paths(inputdir)
  data.addAttrib('part')
  data.addAttrib('path')
  for f in aset:
    annotation = annotatefunction(f)
    if annotation:
      (key, attribs) = annotation
      for k in attribs.keys():
        if not k in data.keys:
          data.addAttrib(k)
      data.add(key, attribs)
    if saveEach:
      data.save()
      
  if raw_input('Save to datafile? (y/n)') is 'y':
    data.save()
  else:
    backup = datafile + '.bak'
    data.save(backup)
    print 'A datafile of this session was stored in {0}'.format(backup)

