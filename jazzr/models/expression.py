import math

def train(corpus):
  pass

def test2():
  from jazzr.corpus import annotations
  corpus = annotations.corpus('explicitswing')
  for song, parse in corpus:
    print 'Name: {0}. Length {1}.'.format(song.name, len(song))
    try:
      test(parse)
    except:
      print "Failed"

def test(parse):
  phi = getFeatures(parse)
  abs_devs = {}
  devs = {}
  ratios = {}
  logratios = {}
  for (level, abs_dev, dev, ratio) in phi:
    abs_devs[(level, )] = abs_devs.get((level, ), []) + [abs_dev]
    devs[(level, )] = devs.get((level, ), []) + [dev]
    ratios[(level, )] = ratios.get((level, ), []) + [ratio]
    if ratio < 0:
      print "warning, ratio smaller than zero"
      ratio = abs(ratio)
    logratios[(level, )] = logratios.get((level, ), []) + [math.log(ratio)]
  for level in sorted(ratios.keys()):
    print '\tLevel {0}.\n\tAbs dev: mu={1}, s={2}.\n\tDev: mu={3}, s={4}.\n\tRatio: mu={5}.'.format(\
        level, mu(abs_devs[level]), std(abs_devs[level]), mu(devs[level]), std(devs[level]), math.exp(mu(logratios[level])))

def mu(list):
  return sum(list)/float(len(list))
          

def std(list):
  mu = sum(list) / float(len(list))
  std = 0.0
  for item in list:
    std += math.pow(mu - item, 2)
  std /= float(len(list))
  return std

def getFeatures(S, downbeat=None, nextDownbeat=None, length=None, level=0):
  division = len(S.children)

  if downbeat == None and length==None:
    downbeat = S.perf_beats[0]
    length = division * (S.perf_beats[1] - S.perf_beats[0])
    nextDownbeat = downbeat + length

  obs = []

  implied_beatLength = length / float(division)
  beatLength = implied_beatLength
  time = downbeat
  if S.perf_beats[0] != None:
    time = S.perf_beats[0]
  if S.hasLength():
    beatLength = S.perf_beats[1] - S.perf_beats[0]

  if S.children[0].isSymbol():
    upbeat = downbeat+beatLength
    if S.perf_beats[1] != None:
      upbeat = S.perf_beats[1]
    newobs = getFeatures(S.children[0], downbeat=downbeat, nextDownbeat=upbeat, length=beatLength, level=level+1)
    obs += newobs

  time += implied_beatLength
  for child, onset, i in zip(S.children[1:], S.onsets[1:], range(1, division)):
    if onset != None:
      on = onset.annotation.perf_onset(onset.index)
      abs_deviation = (on - time)
      deviation = abs_deviation/float(implied_beatLength)
      ratio = ((on - downbeat) / float(i)) /\
          ((nextDownbeat - on) / float(division - i))
      obs.append((level, abs_deviation, deviation, ratio))
    if child.isSymbol():
      newobs = getFeatures(child, downbeat=time, nextDownbeat=nextDownbeat, length=beatLength, level=level+1)
      obs += newobs
    time += implied_beatLength
  return obs
