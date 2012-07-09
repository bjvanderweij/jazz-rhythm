from jazzr.rhythm import groupingparser as gp
from jazzr.corpus import annotations
import math, os

def latexify(S, depth=0):
  if S.isOnset():
    print '[ .$\\bullet$ ] ',
  elif S.isTie():
    print '[ .$*$ ] ',
  if S.isSymbol():
    print '[ .{0} '.format(1/math.pow(2, depth))
    for child in S.children:
      latexify(child, depth=depth+1)
    print '] '

def latexify_list(L, depth=0):
  if L == 'on':
    print '[ .$\\bullet$ ] ',
  elif L == 'tie':
    print '[ .$*$ ] ',
  else:
    print '[ .$\\frac{{1}}{{{0}}}$ '.format(int(math.pow(2, depth))),
    for child in L:
      latexify_list(child, depth=depth+1)
    print '] ',
  
def run():
  corpus = annotations.loadAll()
  import datetime
  time = str(datetime.datetime.now())
  os.mkdir(time)
  # Set some parameters of the parser
  gp.corpus = True
  gp.tolerance = 0.0001

  for annotation in corpus:
    print annotation.name
    notes = []
    if len(annotation) < 5:
      continue
    correction = annotation.position(0)
    for i in range(len(annotation)):
    #for i in range(10):
      if annotation.type(i) in [annotation.NOTE, annotation.END]:
        if annotation.type(i) == annotation.END and annotation.barposition(annotation.position(i)) != 0:
          print 'Warning, end marker note not on beginning of bar'
        notes.append(annotation.position(i) - correction)
    powers = [math.pow(2, x) for x in range(10)]
    bars = annotation.bar(annotation.position(-1) - correction)
    if bars not in powers:
      print 'Correcting bar count from {0} to '.format(bars),
      for power in powers:
        if bars < power:
          notes[-1] = float(power) * 4.0
          print '{0}'.format(power)
          break

    N = gp.preprocess(notes)
    n = len(N)
    chart = gp.parse(N)
    parses = chart[0, n]
    results = []
    for parse in parses:
      results.append((parse.depth, latexify_list(gp.tree(parse))))

    version = 0
    while os.path.exists('{0}/{1}-{2}-parses.txt'.format(time, annotation.name, version)):
      version += 1

    out = open('{0}/{1}-{2}-parses.txt'.format(time, annotation.name, version), 'w')
    for result in sorted(results, key=lambda x: x[0]):
      out.write('{0}:{1}\n'.format(result[0], result[1]))
    out.close()

if __name__ == '__main__':
  run()
  

