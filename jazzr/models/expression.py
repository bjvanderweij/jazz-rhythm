import math
from jazzr.tools import latex
from jazzr.annotation import Annotation
from jazzr.models import pcfg

def additive_noise(std):
  model = {}
  for level in range(1, 10):
    model[(level, 2)] = (0.0, std)
    model[(level, 3)] = (0.0, std)
  return model


def train(corpus):
  features = {}
  for annotation, parse in corpus:
    #print annotation.name
    obs = observations(parse, performance=True)
    for f, expression in obs:
      features[f] = features.get(f, []) + [expression]
  model = {}
  for f, phi in features.iteritems():
    model[f] = (mu(features[f]), std(features[f]))
  return model

def outliers(corpus):
  outliers = {}
  levelcounts = {}
  for annotation, parse in corpus:
    obs = observations(parse, performance=True)
    for f, expression in obs:
      if abs(expression) > math.log(2.0):
        outliers[f] = outliers.get(f, 0) + 1
      levelcounts[f] = levelcounts.get(f, 0) + 1
  return outliers, levelcounts

def mu(list):
  return sum(list)/float(len(list))
          

def std(list):
  mu = sum(list) / float(len(list))
  std = 0.0
  for item in list:
    std += math.pow(mu - item, 2)
  std /= float(len(list))
  return std

def observations(S, downbeat=None, est_nextDownbeat=None, nextDownbeat=None, level=0, parent=None, performance=False, verbose=False):
  division = len(S.children)
  beats = S.beats[:]
  onsets = []
  for s in S.onsets:
    if s != None:
     onsets.append(s.on)
    else:
      onsets.append(None)
  if performance:
    beats = S.perf_beats[:]
    onsets = []
    for s in S.onsets:
      if s != None:
        onsets.append(s.annotation.perf_onset(s.index))
      else:
        onsets.append(None)

  if downbeat == None and est_nextDownbeat == None:
    if beats[1] == None or beats[0] == None: return []
    downbeat = beats[0]
    est_nextDownbeat = downbeat + division * (beats[1] - beats[0])

  if beats[0] != None:
    downbeat = beats[0]

  onsets.append(nextDownbeat)

  if nextDownbeat == None:
    nextDownbeat = est_nextDownbeat

  length = nextDownbeat - downbeat
  obs = []

  for child, beat, i in zip(S.children, beats, range(0, division)):
    #if beat != None and i != 0:
    if S.onsets[i] != None and beat != None and i != 0:
      obs.append((features(S), expressionRatio(downbeat, nextDownbeat, onsets[i], i, division)))
      if obs[-1][1] > abs(math.log(2)) and verbose:
        parentbeats = parent.beats
        temp_onsets = []
        for onset in S.onsets:
          if onset != None:
            if performance:
              temp_onsets.append((onset.annotation.perf_onset(onset.index), onset.index, onset.on))
            else:
              temp_onsets.append(onset.on)
          else:
            temp_onsets.append(None)
        onsets.append(onsets[-1])
        if performance:
          parentbeats = parent.perf_beats
        print '_________________________________________________________________________'
        print 'Ratio: {0}. Level {1}'.format(math.exp(obs[-1][-1]), level)
        print 'Beat: {0}, parent beats: {1}, node beats: {2} node onsets: {3}'.format(beat, parentbeats, beats, temp_onsets)
        print 'Index: {0}, division: {1}, downbeat: {2}, nextDownbeat: {3}'.format(i, division, downbeat, nextDownbeat)
        #latex.view_symbols([S, parent], showOnsets=True, showFeatures=True, scale=False)
    if child.isSymbol():
      b = downbeat + length * i/float(division)
      if beat != None:
        b = beat
      est_upbeat = b + length / float(division)
      upbeat = onsets[i+1]
      if verbose > 1:
        print "Calling observations at level {0}. Beat {1}. Downbeat: {2}, est_upbeat: {3}, upbeat: {4}.".format(level, i, b, est_upbeat, upbeat)
      newobs = observations(child, downbeat=b, est_nextDownbeat=est_upbeat, nextDownbeat=upbeat, level=level+1, parent=S, performance=performance, verbose=verbose)
      obs += newobs
  return obs

def f_measure(results):
  p, r = measure(results)
  return 2*(p*r)/float(p+r)

def expressionRatio(downbeat, nextDownbeat, onset, position, division):
  if nextDownbeat - onset <= 0 or onset - downbeat <= 0:
    ratio = 9999.9
  else:
    ratio = ((onset - downbeat) / float(position)) /\
        ((nextDownbeat - onset) / float(division - position))
  return math.log(ratio)

def features(S):
  depth = S.depth
  if depth > 4:
    depth = 4
  #rule = pcfg.ruleType(S)
  return (depth, len(S.children))

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

