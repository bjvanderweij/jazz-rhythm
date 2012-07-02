from jazzr.rhythm import grammar
from jazzr.rhythm.grammar import NonTerminal, Terminal
import math

maxdepth = 5
IOI = 0
TIE = 1
SYMB = 2

def preprocess(onsets):
  N = []
  for a, b in zip(onsets[0:-1], onsets[1:]):
    N.append((b-a, None, IOI))
  return N

def probability(S):
  threshold = 0.0
  (l, children, type) = S
  if l > math.pow(2, maxdepth):
    return 0.0
  if not S[1]: return 1.0

  length = children[0][0]
  for child in children[1:]:
    if abs(child[0] - length) > threshold:
      return 0.0
  return 1.0

def group(S):
  if len(S) == 1:
    # Either the other note is an onset:
    length = S[0][0]
    return (2*length, [(length, None, TIE), S[0]], SYMB)
  elif len(S) == 2:
    return (S[0][0] + S[1][0], S, SYMB)
  elif len(S) == 3:
    # Not supported yet
    pass
  return None

def hypotheses(S, beam=0.5):
  result = []
  if len(S) == 1:
    pass
  elif len(S) == 2 and S[0][2] == IOI and S[1][2] == IOI:
    p = 1.0
    s = S[1]
    peakReached = False
    if S[1][1] > S[0][1]:
        peakReached = True
    while True:
      H = group([S[0], s])
      print H
      p = probability(H)
      if p > beam:
        result.append(H)
        s = group([S[1]])
      else: break
  elif len(S) == 2:
    H = group(S)
    if probability(H) > beam:
      result.append([H])
  elif len(S) == 3:
    # Not supported yet
    pass
  return result

def close(S, beam=0.5):
  cell = []
  unseen = []
  while True:
    # Get the heads of the trees in S
    #unseen += hypotheses(S, beam=beam)
    #print unseen
    s = group(S)
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
  # Iterate over rows
  for j in range(1, n+1):
    # Fill diagonal cells
    t[j-1, j] = [N[j-1]] + close([N[j-1]], beam=beam)
    # Iterate over columns
    for i in range(j-2, -1, -1):
      print 'Filling ({0}, {1}) '.format(i, j),
      cell = []
      for k in range(i+1, j):
        for B in t[i,k]:
          for C in t[k,j]:
            cell += close([B,C], beam=beam)
      t[i,j] = cell
      print '{0} hypotheses'.format(len(cell))
  return t

def tree(S, one=None):
  types = ['on', 'tie', 'symb']
  if not one:
    one = S[0]
  if not S[1]:
    return types[S[2]]
  return [tree(child, one) for child in S[1]]
  #return [S[0]/float(one), [tree(child, one) for child in S[1]]]

