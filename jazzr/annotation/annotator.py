# Tasks:
# Sort files (or add metadata):
#   - By part (bass/chords/melody/percussion)
#   - By style
#   - By whether it contains swing
# Annotate files:
#   - Metadata
#   - Rhythm
# Store files:
#   - Save tracks, song and metadata
import os, sys, corpus, pickle

# A song entry contains a list of track entries
class SongEntry(list):

  def __init__(self, filename, path, style=None):
    self.filename = filename
    self.path = path
    self.style = None
    list.__init__(self)

class TrackEntry:

  # Rhythm values
  EVEN=0
  SWING=1

  # Part values
  PERCUSSION=0
  BASS=1
  COMP=2
  SOLO=3

  # Instrument values


  def __init__(self, song, n, path=None, part=None, instrument=None, rhythm=None):
    self.filename = filename
    self.path = path
    self.style = None
    list.__init__(self)

def create_metadata(datafile='corpus.txt'):
  if os.path.exists(datafile):
    a = raw_input('File {0} exists, overwrite? (y/n) '.format(datafile)
    if not a is 'y': return
    print 'Creating backup'
    os.system('mv {0} {0}.bak'.format(datafile))
  f = open(datafile, 'w')
  
  metadata = {}
  keys = corpus.names()
  for key in keys:
    metadata[key] = SongEntry('{0}.mid'.format(key), '{0}/{1}.mid'.format(corpus.path, key), style=None)




def load_metadata(datafile='corpus.txt'):
