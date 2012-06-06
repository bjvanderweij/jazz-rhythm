#!/usr/bin/python

from jazzr.corpus import files, filter
from jazzr.annotation import data
from jazzr.annotation import annotator
from jazzr.annotation import tool
from jazzr.tools import commandline
from jazzr.tools import rbsearch
from jazzr.midi import player
from jazzr.rhythm import grid
import code, time, os, datetime


datafile = 'data/corpus.csv'
corpuspath = 'data/corpus/filtered/'

rbindex_raw = 'data/realbooks/RB_INDEX.TXT' 
rbindex2_raw = 'data/realbooks/rawindex.csv' 
rbindex = 'data/realbooks/index.csv' 
rbindex2 = 'data/realbooks/index2.csv' 
rbpath = 'data/realbooks/'

dontreplace = True

choice = -1
d = None

def quickndirty():
  print grid.create_grid(4, 5, spacing=1)

def testtool():
  t = tool.Tool()
  t.annotator()

def annotate(): annotator.simpleAnnotator(corpuspath, datafile)

def parse_index(): 
  # Parse the first raw data file into index2
  rbsearch.parse_file(rbindex_raw, rbindex2)
  # Parse the second raw data file and read index2 and combine then in index
  rbsearch.parse_rawindex(rbindex2_raw, rbindex2, rbindex)


def search(): rbsearch.interactive(rbindex, 'data/realbooks/songs/')

def midiplayer():
  p = player.Player()
  #p.startcommandline()
  p.startgui()

def split(): 
  index = rbsearch.load_file(rbindex)
  counter = 1
  times = []
  for song in index.keys():
    print '[{0}/{1}] '.format(counter, len(index)), 
    if not times == []:
      timeleft = sum(times) / float(len(times)) * (len(index) - counter)
      print 'Estimated time left: {0}'.format(str(datetime.timedelta(seconds=int(timeleft)))),
    print
    counter += 1
    for book in index[song].keys():
      if index[song][book]:
        path = 'data/realbooks/songs/{0}-{1}.pdf'.format(song.replace(' ', '_'), book)
        if os.path.exists(path) and dontreplace:
          print 'Skipping {0} because it already exists'.format(path)
          continue
        start = time.time()
        path = path.replace('\'', '\\\'')
        rbsearch.save(index, rbpath, song, book, path, uninterrupted=True)
        elapsed = time.time() - start
        times.append(elapsed)

def preprocess():
  print "Preprocessing corpus"
  print "(1/2) Expanding multichannel files"
  filter.expandchannels(files.paths(), 'data/corpus/expanded_channels/')
  filter.filtertracks('data/corpus/expanded_channels/', 'data/corpus/filtered/')

  

def review_datafile():
  d = data.Data(datafile)
  for item, attribs in d.data.iteritems():
    print '{0}'.format(item)
    for key, value in attribs.iteritems():
      print '\t{0}: {1}'.format(key, value)

def shell(): code.interact(local=locals())

def quit(): exit(0)

options = [\
('Annotate', annotate),\
('Run quick \'n dirty tests', quickndirty),\
('Test annotation tool', testtool),\
('Start midiplayer', midiplayer),\
('Review datafile', review_datafile),\
('Search realbooks', search),\
('Preprocess and filter corpus', preprocess),\
('Drop to shell', shell),\
('Quit', quit)]

#('Parse realbook index', parse_index),\
#('Parse realbook index (NEW)', parse_newindex),\
#('Search realbooks', search),\
#('Drop to shell', shell),\
#('Split realbooks', split),\
#('Review datafile', review_datafile),\

while True:
  commandline.menu('What shall we do?', options, executableOptions=True)

