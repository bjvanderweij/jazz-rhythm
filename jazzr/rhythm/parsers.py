from jazzr.rhythm.symbol import *
from jazzr.corpus import annotations
from jazzr.models import treeconstraints, pcfg
from jazzr.tools import latex
import transcription
import math

class Parser(object):

  def __init__(self, beam=0.5):
    self.beam = beam
    self.verbose=False

  def probability(self, H):
    """To be implemented by subclass."""
    return 1.0

  def close(self, items):
    cell = []
    unseen = []
    while True:
      p = 1.0
      symbols = []
      for s in items:
        p *= s[1]
        symbols.append(s[0])
      hypotheses = self.group(symbols)
      for h in hypotheses:
        probability = self.probability(h)
        if probability > self.beam:
          unseen += [(h, probability)]
      if unseen == []:
        break
      items = [unseen.pop()]
      cell += items
    return cell

  def group(self, S):
    result = []
    if len(S) == 1:
      if S[0].isOnset():
        result += [Symbol.fromSymbols([Tie()] + S)]
      elif S[0].isSymbol():
        result += [Symbol.fromSymbols([Tie()] + S), Symbol.fromSymbols(S + [Tie()])]
    elif len(S) == 2:
      result += [Symbol.fromSymbols(S)]
      # Triple division
      if S[0].isSymbol() and len(S[0].children) == 2:
        # Only allow triple divisions at note level to parse the corpus efficiently:
        # If triple divisions into symbols were allowed, the children of S[0] need to be upgraded a level
        # (Their ties need to be multiplied by two)
        if S[1].isOnset() and S[0].children[0].isOnset() and S[0].children[1].isOnset():
          result += [Symbol.fromSymbols(S[0].children + [S[1]])]
    elif len(S) == 3:
      # Not supported yet
      pass
    return result

  def parse(self, N):
    n = len(N)
    t = {}
    print "Input length {0}".format(n)
    # Iterate over rows
    for j in range(1, n+1):
      # Fill diagonal cells
      t[j-1, j] = [N[j-1]] + self.close([N[j-1]])
      # Iterate over columns
      for i in range(j-2, -1, -1):
        if self.verbose:
          print 'Filling ({0}, {1}) '.format(i, j),
        cell = []
        for k in range(i+1, j):
          for B in t[i,k]:
            for C in t[k,j]:
              cell += self.close([B,C])
        t[i,j] = cell
        if self.verbose:
          print '{0} hypotheses'.format(len(cell))
    return t

  def profile():
    import cProfile
    cProfile.run('from jazzr.rhythm import groupingparser as gp; gp.parse(gp.preprocess([0, 1, 2, 4, 6]))', 'parseprof')
    import pstats
    p = pstats.Stats('parseprof')
    p.sort_stats('time')
    p.print_stats()

  def list_to_onsets(self, onsets):
    N = []
    lastonset = 0
    for a, b in zip(onsets[0:-1], onsets[1:]):
      N.append(Onset(lastonset, a, b))
      lastonset = a
    return N

  def parse_onsets(self, onsets):
    N = self.list_to_onsets(onsets)
    return self.parse(N)[0, len(N)]

  def parse_annotation(self, a, begin=0, end=None):
    if end == None:
      end = len(a)
    N = []
    lastonset = 0
    # Annotations should start on the first beat of a measure with either a rest or an onset
    correction = a.position(0)
    notes = []
    # Filter out onsets and end markers
    counter = 0
    for i in range(len(a)):
    #for i in range(10):
      if a.type(i) in [a.NOTE, a.END] and counter >= begin and counter < end:
        if a.type(i) == a.END and a.barposition(a.position(i)) != 0:
          print 'Warning, end marker note not on beginning of bar'
        notes.append((a.position(i) - correction, i))
      counter += 1
    powers = [math.pow(2, x) for x in range(10)]
    bars = a.bar(a.position(-1) - correction)
    if bars not in powers:
      print 'Correcting bar count from {0} to '.format(bars),
      for power in powers:
        if bars < power:
          notes[-1] = (float(power) * 4.0, 0)
          print '{0}'.format(power)
          break
    N = []
    lastonset = 0
    for (x, i), (y, j) in zip(notes[0:-1], notes[1:]):
      N.append(Onset(lastonset, x, y, annotation=a, index=i))
      lastonset = x
    return parse(N)[0, len(N)]

class StochasticParser(Parser):

  def __init__(self):
    corpus = annotations.corpus()
    self.model = pcfg.train(corpus)
    self.allowed = treeconstraints.train(corpus)
    self.n = 20
    self.beam = 0.5
    # Standard deviation expressed in proportion of beatlength
    self.std = 0.1
    super(StochasticParser, self).__init__(beam=self.beam)

  def likelihood(self, mu, sigma, x):
    if sigma == 0.0:
      if mu == x: return 1.0
      else: return 0.0
    #return 1/(sigma * math.sqrt(2*math.pi)) * math.exp(-math.pow((mu-x), 2) / float(2*sigma*sigma))
    # Normalised likelihood
    return math.exp(-math.pow((mu-x), 2) / float(2*sigma*sigma))

  def beats_likelihood(self, S, start, length):
    std = self.std * length

    if not S.hasLength():
      (pos, (previous, on, next)) = S.features
      return self.likelihood(start + pos * length, std, on), 1

    p = 1.0
    n = 0
    implied_beatLength = length / float(len(S.children))
    beatLength = S.beats[1] - S.beats[0]
    #beatLength = S.length / float(len(S.children))
    time = start
    #time = S.downbeat()
    for child, beat in zip(S.children, S.beats):
      #if child.hasLikelihood():
        #p *= child.likelihood
      #else:
      #  p *= self.beats_likelihood(child, time, beatLength)
      if child.isOnset():
        p *= self.likelihood(time, self.std, child.on)
        n += 1
      elif child.isTie():
        p *= self.likelihood(time, self.std, beat)
        n += 1
      else:
        prob, count = self.beats_likelihood(child, time, beatLength)
        p *= prob
        n += count
      time += implied_beatLength
    return p, n

  def probability(self, S):
    if not S.hasLength():
      if not S.tree() in self.allowed:
        return 0.0, 1
      return 1.0, 1

    # If time is greater than previous, all is fine, if time is smaller that previous, it becomes increasingly less probable
    # If time is smaller than next, all is fine, if time is greater than next, it becomes increasingly less probable
    start = S.downbeat()
    (pos, (previous, on, next)) = S.features
    if previous - start > 0.5 * S.length or\
        (start + S.length) - next > 0.5 * S.length:
      return 0.0, 1

    return self.beats_likelihood(S, S.downbeat(), S.length)
    
  def close(self, symbols):
    cell = []
    unseen = []
    while True:
      p = 1.0
      prior = 1.0
      for s in symbols:
        prior *= s.prior
      hypotheses = self.group(symbols)
      for h in hypotheses:
        likelihood, n = self.probability(h)
        prior *= self.model[pcfg.ruleType(h)]
        if likelihood > 0.0:
          if math.exp(math.log(likelihood) / float(n)) > self.beam:
            h.likelihood = likelihood
            h.prior = prior
            unseen += [h]
      if unseen == []:
        break
      symbols = [unseen.pop()]
      cell += symbols
    return cell

  def parse(self, N):
    n = len(N)
    t = {}
    print "Input length {0}".format(n)
    # Iterate over rows
    for j in range(1, n+1):
      # Fill diagonal cells
      t[j-1, j] = [N[j-1]] + self.close([N[j-1]])
      # Iterate over columns
      for i in range(j-2, -1, -1):
        if self.verbose:
          print 'Filling ({0}, {1}) '.format(i, j),
        cell = []
        for k in range(i+1, j):
          for B in t[i,k]:
            for C in t[k,j]:
              cell += self.close([B,C])
        if len(cell) > self.n:
          cell = [item for item in sorted(cell, key=lambda x: x.prior * x.likelihood, reverse=True)][:self.n]
        t[i,j] = cell
        if self.verbose:
          print '{0} hypotheses'.format(len(cell))
    return t

class SimpleParser(Parser):

  def __init__(self, corpus=False, allowed=None, tolerance=0.0, maxdepth=5):
    self.corpus = corpus
    self.allowed = allowed
    self.tolerance = tolerance
    self.maxdepth = maxdepth
    self.verbose = False
    super(SimpleParser, self).__init__()
    
  def bottomlevel(self, S):
    if not S.isSymbol():
      return False
    for c in S.children:
      if not c.isOnset():
        return False
    return True

  def probability(self, S):
    p = 1.0
    if self.allowed != None:
      if not S.hasLength() and not S.tree() in self.allowed:
        return 0.0
    if not S.hasLength():
      if S.depth > self.maxdepth:
        if self.verbose > 1:
          print 'Rejected -1'
        return 0.0
      return 1.0

    tolerance = self.tolerance * S.length

    # A hack to parse the corpus efficiently
    if abs(S.length * 2.0 - round(S.length * 2.0)) > 0.0001 and self.corpus:
      if abs(S.length * 3.0 - round(S.length * 3.0)) > 0.0001:
        if self.verbose > 1:
          print 'Rejected 0'
        return 0.0

    (position, (previous, on, next)) = S.features
    if self.verbose > 1:
      print S.features
    if previous - (on - position * S.length) > tolerance:
      if self.verbose > 1:
        print 'Rejected 1'
      return 0.0
    elif (on + (1-position) * S.length) - next > tolerance:
      if self.verbose > 1:
        print 'Rejected 2'
      return 0.0
    childLength = S.length / float(len(S.children))
    currentposition = 0.0
    for child in S.children:
      # Check if the onsets are right
      time = on + (currentposition - position) * S.length
      currentposition += 1/float(len(S.children))
      if child.isSymbol():
        (childposition, (previous, on, next)) = child.features
        if abs(on - (time + childposition * childLength)) > tolerance:
          if self.verbose > 1:
            print 'Rejected 3'
          return 0.0
      elif child.isOnset():
        if abs(time - child.on) > tolerance:
          if self.verbose > 1:
            print 'Rejected 4'
          return 0.0
      # Check if the ratio is right
      if child.hasLength():
        if abs(childLength - child.length) > tolerance:
          if self.verbose > 1:
            print 'Rejected 5'
          return 0.0
    return 1.0

  def parse_best_n(N, window, rating_function):
    n = len(N)
    t = {}
    print "Input length {0}".format(n)
    # Iterate over rows
    for j in range(1, n+1):
      # Fill diagonal cells
      t[j-1, j] = [N[j-1]] + close([N[j-1]])
      # Iterate over columns
      for i in range(j-2, -1, -1):
        if self.verbose:
          print 'Filling ({0}, {1}) '.format(i, j),
        cell = []
        for k in range(i+1, j):
          for B in t[i,k]:
            for C in t[k,j]:
              cell += self.close([B,C])
        if len(cell) > n:
          ratings = [(S, rating_function(S)) for S in cell]
          cell = [S for (S, rating) in sorted(ratings, key=lambda x: x[1], reverse=True)][:window]
        t[i,j] = cell
        if self.verbose:
          print '{0} hypotheses'.format(len(cell))
    return t

