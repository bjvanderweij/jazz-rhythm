import math

maxdepth = 4
corpus = False

def preprocess(onsets):
  N = []
  lastonset = 0
  for a, b in zip(onsets[0:-1], onsets[1:]):
    N.append(Onset(lastonset, a, b))
    lastonset = a
    #N.append([b-a, None, IOI, None, 0])
  return N

def probability(S, verbose=False):
  threshold = 0
  if not S.hasLength():
    if S.depth > maxdepth:
      return 0.0
    return 1.0

  # A hack to parse the corpus efficiently
  if S.length * 2.0 != int(S.length * 2) and S.length * 1.5 != int(S.length * 1.5) and corpus:
    return 0.0

  (leftTies, (previous, on, next), rightTies) = S.features
  if previous - (on - leftTies * S.length) > threshold:
    return 0.0
  elif (on + rightTies * S.length) - next > threshold:
    return 0.0
  anchored = False
  time = 0
  #print '---------------------------'
  childLength = S.length / float(len(S.children))
  for child in S.children:
    # Check if the onsets are right
    #print 'Child'
    if not anchored:
      if child.isSymbol():
        (leftTies, (previous, on, next), rightTies) = child.features
        time = on + rightTies * childLength
        #print 'Anchoring at {0} '.format(time)
        anchored = True
      elif child.isOnset():
        time = child.on + childLength
        #print 'Anchoring at {0} '.format(time)
        anchored = True
    else:
      if child.isSymbol():
        (leftTies, (previous, on, next), rightTies) = child.features
        if abs(on - (time + leftTies * childLength)) > threshold:
          #print 'Rejected {0}, {1}, time:{2}, length {3}'.format(S.features, on, time, S.length)
          return 0.0
      elif child.isOnset():
        if abs(child.on - time) > threshold:
          #print 'Rejected {0}, {1}, time:{2}'.format(S.features, child.on, time, S.length)
          return 0.0
      time += childLength
      #print 'New time: {0}'.format(time)
    # Check if the ratio is right
    if child.hasLength():
      if abs(childLength - child.length) > threshold:
        return 0.0

  return 1.0

def group(S):
  result = []
  if len(S) == 1:
    if S[0].isOnset():
      result += [Symbol.fromSymbols(Tie(), S[0])]
    elif S[0].isSymbol():
      result += [Symbol.fromSymbols(Tie(), S[0]), Symbol.fromSymbols(S[0], Tie())]
  elif len(S) == 2:
    result += [Symbol.fromSymbols(S[0], S[1])]
    # Triple division
    if S[1].isSymbol() and len(S[1].children) == 2:
      result += [Symbol.tripleFromSymbols(S[0], S[1])]
  elif len(S) == 3:
    # Not supported yet
    pass
  return result

def close(S, beam=0.5):
  cell = []
  unseen = []
  while True:
    symbols = group(S)
    for s in symbols:
      p = probability(s)
      if p > beam:
        unseen += [s]
    if unseen == []:
      break
    S = [unseen.pop()]
    cell += S
  return cell

def parse(N, beam=0.5):
  n = len(N)
  t = {}
  print "Input length {0}".format(n)
  # Iterate over rows
  for j in range(1, n+1):
    # Fill diagonal cells
    t[j-1, j] = [N[j-1]] + close([N[j-1]], beam=beam)
    # Iterate over columns
    for i in range(j-2, -1, -1):
      #print 'Filling ({0}, {1}) '.format(i, j),
      cell = []
      for k in range(i+1, j):
        for B in t[i,k]:
          for C in t[k,j]:
            cell += close([B,C], beam=beam)
      t[i,j] = cell
      #print '{0} hypotheses'.format(len(cell))
  return t

def profile():
  import cProfile
  cProfile.run('from jazzr.rhythm import groupingparser as gp; gp.parse(gp.preprocess([0, 1, 2, 4, 6]))', 'parseprof')
  import pstats
  p = pstats.Stats('parseprof')
  p.sort_stats('time')
  p.print_stats()


def tree(S):
  types = ['on', 'tie', 'symb']
  if S.isTie() or S.isOnset():
    return types[S.type]
  return [tree(child) for child in S.children]
  #return [S[0]/float(one), [tree(child, one) for child in S[1]]]

class Symbol(object):

  # Types
  ONSET = 0
  TIE = 1
  SYMB = 2
  SONG = 3
  
  #Beats
  ON = 0
  OFF = 1

  def __init__(self, features, length=None, children=None, depth=0, type=SYMB, grid=None):
    self.depth = depth
    self.type = type
    self.children = children
    self.length = length
    self.features = features

  @staticmethod
  def fromSymbols(A, B):
    tiesLeft = 0.0
    tiesRight = 0.0
    previous = -1
    on = -1
    next = -1
    span = None
    if A.isTie():
      tiesLeft += 0.5
    elif A.isOnset():
      previous = A.previous
      on = A.on
      tiesRight += 0.5
      next = A.next
    else:
      (tl, (p, o, n), tr) = A.features
      tiesLeft += tl/2.0
      tiesRight += tr/2.0
      previous = p
      on = o
      next = n
      if A.hasLength():
        span = (0.5, A.length)

    if B.isTie():
      tiesRight += 0.5
    elif B.isOnset():
      next = B.next
      if A.isOnset() or A.isSymbol():
        span = (tiesRight, B.on - on)
        tiesRight += 0.5
      else:
        previous = B.previous
        on = B.on
        tiesRight = 0.5
    else:
      (tl, (p, o, n), tr) = B.features
      next = n
      if A.isOnset() or A.isSymbol():
        tiesRight += tl/2.0
        if not A.hasLength():
          span = (tiesRight, o - on)
        tiesRight += tr/2.0
      else:
        previous = p
        on = o
        tiesLeft += tl/2.0
        tiesRight = tr/2.0
        if B.hasLength():
          span = (0.5, B.length)

    features = (tiesLeft, (previous, on, next), tiesRight)
    length = None
    if span:
      length = (1/float(span[0])) * span[1]
    depth = max(A.depth, B.depth) + 1
    children = [A, B]
    R = Symbol(features, length=length, children=children, depth=depth)
    return R

  @staticmethod
  def tripleFromSymbols(A, B):
    # A is either a tie or an onset and B has two children
    tiesLeft = 0.0
    tiesRight = 0.0
    previous = 0.0
    on = 0.0
    onsetDefined = False
    next = 0.0
    span = None
    if A.isTie():
      tiesLeft += 1/3.0
    elif A.isOnset():
      onsetDefined = True
      previous = A.previous
      on = A.on
      next = A.next
      tiesRight += 1/3.0
    else:
      onsetDefined = True
      (tl, (p, o, n), tr) = A.features
      tiesLeft += tl/3.0
      tiesRight += tr/3.0
      previous = p
      on = o
      next = n
      if A.hasLength():
        span = (1/3.0, A.length)

    for child in B.children:
      if child.isTie():
        if onsetDefined:
          tiesRight += 1/3.0
        else:
          tiesLeft += 1/3.0
      elif child.isOnset():
        next = child.next
        if onsetDefined:
          span = (tiesRight, child.on - on)
          tiesRight += 1/3.0
        else:
          onsetDefined = True
          previous = child.previous
          on = child.on
          tiesRight = 1/3.0
      else:
        (tl, (p, o, n), tr) = child.features
        next = n
        if onsetDefined:
          tiesRight += tl*2/3.0
          span = (tiesRight, o - on)
          tiesRight += tr*2/3.0
        else:
          onsetDefined = True
          previous = p
          on = o
          tiesLeft += tl*2/3.0
          tiesRight = tr*2/3.0
          if child.hasLength():
            span = (1/3.0, child.length)

    features = (tiesLeft, (previous, on, next), tiesRight)
    length = None
    if span:
      length = 1/float(span[0]) * span[1]
    depth = max(A.depth, B.depth) + 1
    children = [A] +  B.children
    R = Symbol(features, length=length, children=children, depth=depth)
    return R
    pass

  def hasLength(self):
    return self.length != None
  
  def isOnset(self):
    return self.type == self.ONSET

  def isTie(self):
    return self.type == self.TIE

  def isSymbol(self):
    return self.type == self.SYMB

  def isSong(self):
    return self.type == self.SONG

class Onset(Symbol):

  def __init__(self, previous, on, next):
    self.previous = previous
    self.on = on
    self.next = next
    super(Onset, self).__init__([], type=Symbol.ONSET)

class Tie(Symbol):

  def __init__(self):
    super(Tie, self).__init__([], type=Symbol.TIE)

