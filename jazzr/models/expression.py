import math
from jazzr.tools import latex
from jazzr.annotation import Annotation

def additive_noise(std):
  model = {}
  for level in range(1, 10):
    model[(level,)] = (0.0, std)
  return model


def train(corpus):
  perdepth = {}
  all = []
  for annotation, parse in corpus:
    #print annotation.name
    obs = observations(parse, performance=True)
    levels = getLevels(obs)
    for (level, ) in sorted(levels):
      logratios = getLogRatios(obs, level)
      depth = parse.depth-level
      perdepth[(depth, )] = perdepth.get((depth, ), []) + logratios
      all += logratios
      #print 'Level {0}. Mu = {1}, sigma = {2}'.format(level, mu(logratios), std(logratios))
  model = {}
  mean = mu(all)
  deviation = std(all)
  for level in range(1, 10):
    model[(level,)] = (mean, deviation)
  #for depth, phi in perdepth.iteritems():
  #  model[depth] = (mu(perdepth[depth]), std(perdepth[depth]))
  return model

def mu(list):
  return sum(list)/float(len(list))
          

def std(list):
  mu = sum(list) / float(len(list))
  std = 0.0
  for item in list:
    std += math.pow(mu - item, 2)
  std /= float(len(list))
  return std

def complexPosition(S, performance=False):
  division = len(S.children)
  for child, p in zip(S.children, range(division)):
    if child.isOnset():
      if performance:
        return (p/float(division), child.annotation.perf_onset(child.index))
      return (p/float(division), child.on)
    elif child.isSymbol():
      pos, on = complexPosition(child, performance=performance)
      if pos != -1:
        return (p/float(division) + pos/float(division), on)
  return -1, 0

def observations(S, length=None, downbeat=None, nextDownbeat=None, score=0, level=0, parent=None, performance=False, verbose=False):
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

  if downbeat == None and nextDownbeat == None:
    if beats[1] == None or beats[0] == None: return []
    downbeat = beats[0]
    nextDownbeat = downbeat + division * (beats[1] - beats[0])
    length = nextDownbeat - downbeat


  onsets.append(None)
  downbeats = []
  complexbeats = []

  for child, pos in zip(S.children, range(division)):
    if onsets[pos] != None:
      downbeats.append((pos, onsets[pos]))
    elif child.isSymbol():
      cpos, con = complexPosition(child, performance=performance)
      complexbeats.append((pos + cpos, con))
  lscore = 2
  if len(downbeats) <= 1:
    lscore = 1
    if len(downbeats) == 0:
      lscore = 0
    downbeats += complexbeats
    downbeats = sorted(downbeats, key=lambda x: x[0])
  spans = []
  for (pos1, on1), (pos2, on2) in zip(downbeats[:-1], downbeats[1:]):
    if pos2 - pos1 == 0:
      spans.append(0)
    else:
      spans.append((on2 - on1)/float(pos2 - pos1))

  if onsets[0] != None:
    downbeat = beats[0]

  if len(spans) > 0 and lscore >= score:
    p, on = downbeats[0]
    length = division * sum(spans)/float(len(spans))
    downbeat = on - length * p/float(division)
    nextDownbeat = downbeat + length
  else:
    length = nextDownbeat - downbeat
    lscore = score

  obs = []

  for child, beat, i in zip(S.children, beats, range(0, division)):
    #if beat != None and i != 0:
    if S.onsets[i] != None and beat != None and i != 0:
      obs.append(features(downbeat, nextDownbeat, onsets[i], i, division, level))
      if abs(math.log(obs[-1][-1])) > abs(math.log(2)) and verbose:
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
        print 'Ratio: {0}. Level {1}, Deviation {2}'.format(obs[-1][-1], level, obs[-1][-2])
        print 'Beat: {0}, parent beats: {1}, node beats: {2} node onsets: {3}'.format(beat, parentbeats, beats, temp_onsets)
        print 'Index: {0}, division: {1}, downbeat: {2}, nextDownbeat: {3}'.format(i, division, downbeat, nextDownbeat)
        #latex.view_symbols([S, parent], showOnsets=True, showFeatures=True, scale=False)
    if child.isSymbol():
      b = downbeat + length * i/float(division)
      if onsets[i] != None:
        b = onsets[i]
      upbeat = b + length / float(division)
      if onsets[i+1] != None:
        lscore = 2
        upbeat = onsets[i+1]
      if verbose > 1:
        print "Calling observations at level {0}. Beat {1}. Downbeat: {2}, upbeat: {3}.".format(level, i, b, upbeat)
      newobs = observations(child, downbeat=b, nextDownbeat=upbeat, level=level+1, parent=S, performance=performance, verbose=verbose, score=lscore)
      obs += newobs
  return obs

def features(downbeat, nextDownbeat, onset, position, division, level):
  time = downbeat + position/float(division) * (nextDownbeat - downbeat)
  beatlength = nextDownbeat - downbeat
  abs_deviation = (onset - time)
  # Annotation errors?
  if beatlength == 0:
    deviation = 0.0
  else:
    deviation = abs_deviation/float(beatlength)
  if nextDownbeat - onset <= 0 or onset - downbeat <= 0:
    ratio = 1.0
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

