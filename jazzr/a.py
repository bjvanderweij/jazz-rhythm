from jazzr.rhythm import groupingparser as gp
from jazzr.rhythm import grammar
from jazzr.corpus import annotations
from jazzr.tools import commandline
#import transcription
import sys, math

notes = []
if len(sys.argv) > 1:
  gp.corpus = False
  notes = [int(x) for x in sys.argv[1:]]
else:
  gp.corpus = True
  annotation = annotations.loadAll()[commandline.menu('', [a.name for a in annotations.loadAll()])]
  correction = annotation.position(0)
  for i in range(len(annotation)):
  #for i in range(10):
    if annotation.type(i) in [annotation.NOTE, annotation.END]:
      if annotation.type(i) == annotation.END and annotation.barposition(i) != 0:
        print 'Warning, end marker note not on beginning of bar'
      notes.append(annotation.position(i) - correction)
  powers = [math.pow(2, x) for x in range(10)]
  bars = annotation.bar(annotation.position(-1) - correction)-1
  if bars not in powers:
    print 'Correcting bar count from {0} to '.format(bars+1),
    for power in powers:
      if bars < power:
        notes[-1] = float(power+1) * 4.0
        print '{0}'.format(power+1)
        break

N = gp.preprocess(notes)
n = len(N)
chart = gp.parse(N)
results = chart[0, n]
test = chart[0, 2]
trees = []
dupes = 0

out = open('test.txt', 'w')
for r in test:
  tree = gp.tree(r)
  if r.hasLength():
    out.write('{0}:\t{1}\n'.format(r.length, tree))
  if tree in trees:
    dupes += 1
  else:
    trees += [tree]
out.write('{0}'.format(dupes))
out.close()

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

exit(0)
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

