#!/usr/bin/python
from jazzr.rhythm import groupingparser as gp
from jazzr.rhythm import grammar
from jazzr.corpus import annotations
from jazzr.tools import commandline, latex
#import transcription
import sys, math

notes = []
if len(sys.argv) > 1:
  notes = [int(x) for x in sys.argv[1:]]
  results = gp.parse_onsets(notes)
else:
  annotation = annotations.loadAll()[commandline.menu('', [a.name for a in annotations.loadAll()])]
  results = gp.parse_annotation(annotation)

latex.view_symbols(results, scale=False)
exit(0)
trees = []
dupes = 0

dupes = 0
for r in results:
  tree = gp.tree(r)
  if tree in trees:
    dupes += 1
  else:
    trees += [tree]

for r in results:
  if r.hasLength():
    print '{0}:\t{1}'.format(r.length, gp.tree(r))
if len(results) > 0:
  analysis = min(results, key=lambda x: x.depth)
  print 'Duplicates: {0}.\nResult: {1}.'.format(dupes, gp.tree(analysis))

#chosen = results[commandline.menu('', [(r.length, gp.tree(r)) for r in results])]
#gp.probability(chosen, verbose=True)

#results = sorted(results, key=lambda x: x[0])
#score = None
#from music21 import stream
#while True:
#  choice = commandline.menu('Choose', [gp.tree(r) for r in results])
#  if choice == -1: break
#  if not score:
#    score = transcription.transcribeTree(results[choice])
#  else:
#    measure = stream.Measure()
#    score.append(transcription.transcribe(results[choice], measure, 0, barlevel=0))
#  score.show()


def printNice(features):
  result = ''
  for feature in features:
    result += '{0}({1}) '.format(feature[0], ', '.join([str(x) for x in feature[1:]]))
  return result


maxdiv = int(sys.argv[1])
notes = [int(x) for x in sys.argv[2:]]
print 'Max division: {0}'.format(maxdiv)
print 'Parsing {0}'.format(notes)
t = cp.musical_cky(notes, maxdiv, boundNotes=True, removeDuplicates=False)
timesignatures = grammar.timesignatures()
print '{0} symbols in cell (0, {1})'.format(len(t[0, len(notes)]), len(notes))
parses = []
trees = {}
dupes = 0
for symbol in t[0, len(notes)]:
  if symbol.symbol in timesignatures:
  #if True:
    tree = symbol.getTree()
    if tree in trees:
      dupes += 1
    else:
      trees[tree] = 1
      parses += [symbol]

i = 0
for symbol in parses:
  tree = symbol.getTree()
  print '[{0}]: {1}'.format(i,  printNice(symbol.features))
  print tree
  i += 1
print '{0} duplicates found'.format(dupes)

