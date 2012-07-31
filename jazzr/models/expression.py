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
  phi = perf_observations(parse)
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

def observations(S, downbeat=None, nextDownbeat=None, level=0, parent=None):
  division = len(S.children)

  if downbeat == None and nextDownbeat == None:
    downbeat = S.beats[0]
    nextDownbeat = downbeat + division * (S.beats[1] - S.beats[0])
    #length = S.length

  if S.beats[0] != None:
    downbeat = S.beats[0]

  length = nextDownbeat - downbeat
  obs = []

  if S.children[0].isSymbol():
    upbeat = downbeat + length / float(division)
    if S.beats[1] != None:
      upbeat = S.beats[1]
    newobs = observations(S.children[0], downbeat=downbeat, nextDownbeat=upbeat, level=level+1, parent=S)
    obs += newobs

  for child, beat, onset, i in zip(S.children[1:], S.beats[1:], S.onsets[1:], range(1, division)):
    if beat != None:
      obs.append(features(downbeat, nextDownbeat, beat, i, division, level))
    if child.isSymbol():
      b = downbeat + i/float(division) * length
      if beat != None:
        b = beat
      newobs = observations(child, downbeat=b, nextDownbeat=nextDownbeat, level=level+1, parent=S)
      obs += newobs
  return obs

def features(downbeat, nextDownbeat, onset, position, division, level):
  time = position/float(division) * (nextDownbeat - downbeat)
  beatlength = (time - downbeat) / float(position)
  abs_deviation = (onset - time)
  if beatlength == 0:
    deviation = 9999.9
  else:
    deviation = abs_deviation/float(beatlength)
  if nextDownbeat - onset <= 0 or onset - downbeat <= 0:
    ratio = 9999.9
  else:
    ratio = ((onset - downbeat) / float(position)) /\
        ((nextDownbeat - onset) / float(division - position))
    if ratio <= 0: print onset, downbeat, nextDownbeat
  return (level, abs_deviation, deviation, ratio)

def perf_observations(S, downbeat=None, nextDownbeat=None, level=0, parent=None):
  division = len(S.children)

  if downbeat == None and nextDownbeat == None:
    downbeat = S.perf_beats[0]
    nextDownbeat = downbeat + division * (S.perf_beats[1] - S.perf_beats[0])
    #length = S.length

  if S.perf_beats[0] != None:
    downbeat = S.perf_beats[0]

  length = nextDownbeat - downbeat
  obs = []

  if S.children[0].isSymbol():
    upbeat = downbeat + length / float(division)
    if S.perf_beats[1] != None:
      upbeat = S.perf_beats[1]
    newobs = perf_observations(S.children[0], downbeat=downbeat, nextDownbeat=upbeat, level=level+1, parent=S)
    obs += newobs

  for child, beat, i in zip(S.children[1:], S.perf_beats[1:], range(1, division)):
    if beat != None:
      obs.append(features(downbeat, nextDownbeat, beat, i, division, level))
    if child.isSymbol():
      b = downbeat + i/float(division) * length
      if beat != None:
        b = beat
      newobs = perf_observations(child, downbeat=b, nextDownbeat=nextDownbeat, level=level+1, parent=S)
      obs += newobs
  return obs

def getLevels(obs):
  levels = {}
  for o in obs:
    levels[(o[0], )] = levels.get((o[0], ), []) + [o]
  return levels

def getRatios(obs, level):
  obs = getLevels(obs)
  ratios = []
  observations = obs[(level, )]
  for o in observations:
    ratios.append(o[3])
  return ratios

def getLogRatios(obs, level):
  ratios = getRatios(obs, level)
  return [math.log(x) for x in ratios]

def getSigma(obs, p, mean, level=None):
  # Calculate the sigma needed to let the per observation likelihood of obs be p under mu=mean
  levels = getLevels(obs)
  if level == None:
    logratios = []
    for l in levels.keys():
      logratios += getLogRatios(obs, l[0])
  else:
    logratios = getLogRatios(obs, level)

  N = float(len(logratios))
  Sum = 0.0
  for r in logratios:
    Sum += math.pow(r-mean, 2)
  sigmaSquare = - Sum / (math.log(p) * 2.0 * N)
  Sum = 0.0
  for r in logratios:
    Sum += math.log(math.exp(-math.pow(mean-r, 2)/(2*sigmaSquare)))

  return math.sqrt(sigmaSquare)



