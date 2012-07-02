from jazzr.rhythm import grammar
from jazzr.rhythm.grammar import NonTerminal, Terminal
import math

maxdepth = 2
IOI = 0
TIE = 1
SYMB = 2

def preprocess(onsets):
  N = []
  for a, b in zip(onsets[0:-1], onsets[1:]):
    N.append([b-a, None, IOI, None, 0])
  return N

def probability(S, length=None):
  threshold = 0
  if S[4] > maxdepth:
    return 0.0
  # If a probability was already defined, return it
  if S[3]:
    return S[3]
  # If length is undefined, try to define it
  if not length:
    if S[0]:
      length = S[0]
    else: 
      return 1.0
  # If this unit doesn't have a length yet, assign it
  if not S[0]:
    S[0] = length
  # If it does, see if it matches the length
  else: 
    if abs(length - S[0]) > threshold:
      return 0.0
    else:
      return 1.0
  # The symbol can now be either a TIE or a SYMB
  if S[2] == TIE:
    return 1.0
  # The symbol must be a SYMB by now and have children
  p = 1.0
  childlength = length / float(len(S[1]))
  for child in S[1]:
    p *= probability(child, length=childlength, depth=depth+1)
  return p

def group(S):
  result = []
  if len(S) == 1:
    # Either the other note is an onset:
    if S[0][2] == IOI:
      #length = S[0][0]
      result += [[None, [[None, None, TIE, None, 0], S[0]], SYMB, None, S[0][4]+1]]
    elif S[0][2] == SYMB:
      result += [[None, [[None, None, TIE, None, 0], S[0]], SYMB, None, S[0][4]+1],\
          [None, [S[0], [None, None, TIE, None, 0]], SYMB, None, S[0][4]+1]]
  elif len(S) == 2:
    # One of the elements may have an undefined length but not both
    #if not (S[0][0] or not S[1][0]) and (S[0][0] or S[1][0]):
    if S[0][0] or S[1][0]:
      if not S[0][0]: S[0][0] = S[1][0]
      elif not S[1][0]: S[1][0] = S[0][0]
      result += [[S[0][0] + S[1][0], S, SYMB, None, max(S[0][4], S[1][4]) + 1]]
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
  # Iterate over rows
  for j in range(1, n+1):
    # Fill diagonal cells
    t[j-1, j] = [N[j-1]] + close([N[j-1]], beam=beam)
    print j-1, j
    for item in t[j-1, j]:
      print tree(item)
    # Iterate over columns
    for i in range(j-2, -1, -1):
      print 'Filling ({0}, {1}) '.format(i, j),
      cell = []
      for k in range(i+1, j):
        for B in t[i,k]:
          for C in t[k,j]:
            cell += close([B,C], beam=beam)
      t[i,j] = cell
      print i, j
      for item in cell:
        print tree(item)
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

