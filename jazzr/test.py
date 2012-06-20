#!/usr/bin/python

from jazzr.corpus import *
from jazzr.annotation import data, annotator, tool, Annotation
import jazzr.annotation as types
from jazzr.tools import commandline, rbsearch, transcriber
from jazzr.midi import player
from jazzr.rhythm import grid, temperley, subdivision
import code, time, os, datetime, random


datafile = '../Data/corpus.csv'
corpuspath = '../Data/corpus/filtered/'

rbindex_raw = '../Data/realbooks/RB_INDEX.TXT' 
rbindex2_raw = '../Data/realbooks/rawindex.csv' 
rbindex = '../Data/realbooks/index.csv' 
rbindex2 = '../Data/realbooks/index2.csv' 
rbpath = '../Data/realbooks/'

dontreplace = True

choice = -1
d = None

def quickndirty():
  corpus = annotations.loadAll()
  #choice = commandline.menu('Choose item', [x[2]['name'] for x in corpus])
  #parse = subdivision.parse(corpus[choice])
  subdivision.train(corpus)


def transcribe():
  corpus = annotations.loadAll()
  choice = commandline.menu('Choose item', [x[2]['name'] for x in corpus])
  annotation = corpus[choice][0]
  notes = corpus[choice][1]
  metadata = corpus[choice][2]
  transcriber.transcribe(annotation, metadata, transpose=1)

def check_corpus():
  threshold = 0.5
  corpus = annotations.loadAll()
  for (annotation, notes, metadata) in corpus:
    print metadata['name']
    for (position, index, pitch, type) in annotation:
      if type == types.NOTE:
       deviation = convert.deviation(position, notes[index][0], metadata)
       if deviation > threshold:
         print "Deviation for {0}, {1}, {2}, {3} is suspiciously large ({4}).".format(position, index, pitch, type, deviation)

def cross_validate():
  songs = 0
  count = 0
  notecount = 0
  corpus = []
  print 'Loading corpus.'
  for song in annotations.songs(): 
    songs += 1
    for version in annotations.versions(song):
      for track in annotations.tracks(song, version):
        count += 1
        metadata, annotation, notes, midifile = annotations.load('annotations', '{0}-{1}-{2}'.format(song, version, track))
        corpus += [(annotation, notes, metadata)]
  print '{0} songs annotated. Total annotations: {1}. Total number annotated items: {2}'.format(songs, count, notecount)
  folds = 5
  n = len(corpus)
  results = []
  for i in range(folds):
    print 'Preparing fold {0} out of {1}'.format(i+1, folds)
    train = []
    test = []
    n_test = int(n/float(folds))
    for j in range(n_test):
      index = int(random.random() * (n-j))
      test += [corpus[index]]
      del corpus[index]
    train = corpus
    
    print 'Training model'
    model = temperley.metrical_position(train)
    print 'Done. Model: {0}'.format(model)
    print 'Evaluating model.'
    cross_ent = 0
    for (annotation, notes, metadata) in test:
      cross_ent += temperley.loglikelihood(annotation, metadata, model)
    cross_ent /= float(n_test)
    print 'Done. Average cross-entropy: {0}'.format(cross_ent)
    results.append(cross_ent)
    corpus = train + test
  result = sum(results)/float(len(results))
  print 'All done. Resulting cross-entropy: {0}'.format(result)


    



def testtool():
  mf = midi.selectfile(collection='melodies')
  t = tool.Tool(mf)
  t.annotator()

def annotate(): annotator.simpleAnnotator(corpuspath, datafile)

def filtermanually(): filter.filtermanually()

def parse_index(): 
  # Parse the first raw data file into index2
  rbsearch.parse_file(rbindex_raw, rbindex2)
  # Parse the second raw data file and read index2 and combine then in index
  rbsearch.parse_rawindex(rbindex2_raw, rbindex2, rbindex)


def search(): rbsearch.interactive(rbindex)

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
  filter.expandchannels(midi.paths(), 'data/corpus/expanded_channels/')
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
('Run quick \'n dirty tests', quickndirty),\
('Test annotation tool', testtool),\
('Check corpus', check_corpus),\
('Search realbooks', search),\
('Drop to shell', shell),\
('Quit', quit)]

#('Run quick \'n dirty tests', quickndirty),\
#('Parse realbook index', parse_index),\
#('Parse realbook index (NEW)', parse_newindex),\
#('Search realbooks', search),\
#('Drop to shell', shell),\
#('Split realbooks', split),\
#('Review datafile', review_datafile),\

while commandline.menu('What shall we do?', options, executableOptions=True) != -1: pass

