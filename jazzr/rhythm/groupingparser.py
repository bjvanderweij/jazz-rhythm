from jazzr.rhythm.symbol import *
import math

maxdepth = 4
tolerance = 0.0
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
  if not S.hasLength():
    if S.depth > maxdepth:
      if verbose:
        print 'Rejected -1'
      return 0.0
    return 1.0

  # A hack to parse the corpus efficiently
  if abs(S.length * 2.0 - round(S.length * 2.0)) > 0.0001 and corpus:
    if abs(S.length * 3.0 - round(S.length * 3.0)) > 0.0001:
      if verbose:
        print 'Rejected 0'
      return 0.0

  (leftTies, (previous, on, next), rightTies) = S.features
  if verbose:
    print S.features
  if previous - (on - leftTies * S.length) > tolerance:
    if verbose:
      print 'Rejected 1'
    return 0.0
  elif (on + rightTies * S.length) - next > tolerance:
    if verbose:
      print 'Rejected 2'
    return 0.0
  anchored = False
  time = 0
  childLength = S.length / float(len(S.children))
  for child in S.children:
    # Check if the onsets are right
    if not anchored:
      if child.isSymbol():
        (leftTies, (previous, on, next), rightTies) = child.features
        time = on + rightTies * childLength
        anchored = True
      elif child.isOnset():
        time = child.on + childLength
        anchored = True
    else:
      if child.isSymbol():
        (leftTies, (previous, on, next), rightTies) = child.features
        if abs(on - (time + leftTies * childLength)) > tolerance:
          if verbose:
            print 'Rejected 3'
          return 0.0
      elif child.isOnset():
        if abs(child.on - time) > tolerance:
          if verbose:
            print 'Rejected 4'
          return 0.0
      time += childLength
    # Check if the ratio is right
    if child.hasLength():
      if abs(childLength - child.length) > tolerance:
        if verbose:
          print 'Rejected 5'
        return 0.0

  return 1.0

def group(S):
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

