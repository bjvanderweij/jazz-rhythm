import math
from jazzr.tools import latex
from jazzr.annotation import Annotation

def train(corpus):
  for annotation, parse in corpus:
    print annotation.name
    obs = observations(parse, performance=True)
    levels = getLevels(obs)
    for (level, ) in sorted(levels):
      logratios = getLogRatios(obs, level)
      print 'Level {0}. Mu = {1}, sigma = {2}'.format(level, mu(logratios), std(logratios))

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
  phi = observations(parse)
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

def observations(S, downbeat=None, nextDownbeat=None, level=0, parent=None, performance=False, verbose=False):
  division = len(S.children)
  beats = S.beats[:]
  if performance:
    beats = S.perf_beats[:]

  if downbeat == None and nextDownbeat == None:
    if beats[1] == None or beats[0] == None: return []
    downbeat = beats[0]
    nextDownbeat = downbeat + division * (beats[1] - beats[0])

  beats.append(nextDownbeat)
  if beats[0] != None:
    downbeat = beats[0]
  length = nextDownbeat - downbeat
  obs = []

  for child, beat, i in zip(S.children, beats, range(0, division)):
    if beat != None and i != 0:
      obs.append(features(downbeat, nextDownbeat, beat, i, division, level))
      if abs(math.log(obs[-1][-1])) > abs(math.log(2)) and verbose:
        parentbeats = parent.beats
        onsets = []
        for onset in S.onsets:
          if onset != None:
            if performance:
              onsets.append((onset.annotation.perf_onset(onset.index), onset.index, onset.on))
            else:
              onsets.append(onset.on)
          else:
            onsets.append(None)
        if performance:
          parentbeats = parent.perf_beats
        print '_________________________________________________________________________'
        print 'Ratio: {0}. Level {1}'.format(obs[-1][-1], level)
        print 'Beat: {0}, parent beats: {1}, node beats: {2} node onsets: {3}'.format(beat, parentbeats, beats, onsets)
        print 'Index: {0}, division: {1}, downbeat: {2}, nextDownbeat: {3}'.format(i, division, downbeat, nextDownbeat)
        #latex.view_symbols([S, parent], showOnsets=True, showFeatures=True, scale=False)
    if child.isSymbol():
      b = downbeat + length * i/float(division)
      if beat != None:
        b = beat
      upbeat = b + length * 1 / float(division)
      #if beats[i+1] != None:
      #  upbeat = beats[i+1]
      newobs = observations(child, downbeat=b, nextDownbeat=upbeat, level=level+1, parent=S, performance=performance, verbose=verbose)
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
  #return (level, abs_deviation, deviation, ratio)
  return (level, abs_deviation, deviation, ratio)

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
  if sigmaSquare == 0.0:
    return 0.0
  Sum = 0.0
  for r in logratios:
    Sum += math.log(math.exp(-math.pow(mean-r, 2)/(2*sigmaSquare)))
  return math.sqrt(sigmaSquare)


def getMaxSigma(S, p, mean, level=None, performance=False):
  obs = observations(S)
  if performance:
    obs = observations(S, performance=performance)
  if obs == []:
    return [0]
  s = [getSigma(obs, p, mean, level=level)]
  for child in S.children:
    if child.isSymbol():
      s += getMaxSigma(child, p, mean, level=level, performance=performance)
  return [max(s)]

