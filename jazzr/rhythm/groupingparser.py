from jazzr.rhythm import grammar
from jazzr.rhythm.grammar import NonTerminal, Terminal
import math

maxdepth = 4
IOI = 0
TIE = 1
SYMB = 2

def preprocess(onsets):
  N = []
  for on in onsets:
    N.append(Onset(on))
    #N.append([b-a, None, IOI, None, 0])
  return N

def probability(S, verbose=False):
  threshold = 0
  if S.depth > maxdepth:
    return 0.0
  if not S.hasGrid():
    return 1.0
  start = 0
  anchored = False
  time = 0
  # Over complicated code to get an IOI from a series of notes and ties
  for (note, beat, depth) in S.notes:
    if not anchored and note.isOnset():
      start = note.on
      anchored = True
    elif note.isOnset():
      if abs(note.on - (start+time)) > threshold:
        #print S.grid.getLength(0, 0)
        #print 'prob:', start, note.on, start+time
        return 0.0
    time += S.grid.getLength(beat, depth)  
  for level in S.grid.levels.keys():
    pass
  return 1.0

def probability2(S, length=None):
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
    if S[0].isOnset():
      #length = S[0][0]
      result += [Symbol.fromSymbols(Tie(), S[0])]
    elif S[0].isSymbol():
      result += [Symbol.fromSymbols(Tie(), S[0]), Symbol.fromSymbols(S[0], Tie())]
  elif len(S) == 2:
    result += [Symbol.fromSymbols(S[0], S[1])]
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
    #print j-1, j
    #for item in t[j-1, j]:
    #  print tree(item)
    # Iterate over columns
    for i in range(j-2, -1, -1):
      print 'Filling ({0}, {1}) '.format(i, j),
      cell = []
      for k in range(i+1, j):
        for B in t[i,k]:
          for C in t[k,j]:
            cell += close([B,C], beam=beam)
      t[i,j] = cell
      #print i, j
      #for item in cell:
      #  print tree(item)
      print '{0} hypotheses'.format(len(cell))
  return t

def tree(S):
  types = ['on', 'tie', 'symb']
  if not S.isSymbol():
    return types[S.type]
  return [tree(child) for child in S.children]
  #return [S[0]/float(one), [tree(child, one) for child in S[1]]]

class Symbol(object):

  # Types
  ONSET = 0
  TIE = 1
  SYMB = 2
  
  #Beats
  ON = 0
  OFF = 1

  #Intervals
  ON_OFF = 0
  ON_ON = 1
  OFF_OFF = 2
  OFF_ON = 3

  def __init__(self, notes=[], length=-1, probability=-1, children=None, depth=0, type=SYMB, grid=None):
    self.length = length
    self.probability = probability
    self.depth = depth
    self.type = type
    self.children = children
    self.grid = grid
    self.notes = notes

  @staticmethod
  def fromSymbols(A, B):
    notesA = []
    notesB = []
    # This labels the notes as on or off beats
    # (which is not a property of the note itself
    # but a result of the derivation)
    if A.isOnset() or A.isTie():
      notesA = [(A, Symbol.ON, 1)]
    else:
      for note in A.notes:
        notesA += [(note[0], note[1], note[2]+1)]

    if B.isOnset() or B.isTie():
      notesB = [(B, Symbol.OFF, 1)]
    else:
      for note in B.notes:
        notesB += [(note[0], note[1], note[2]+1)]
    notes = notesA + notesB
    depth = max(A.depth, B.depth) + 1
    children = [A, B]
    R = Symbol(grid=Grid.getGrid(A, B, notes), notes=notes, children=children, depth=depth)
    return R

  def hasGrid(self):
    return self.grid != None
  
  def isOnset(self):
    return self.type == self.ONSET

  def isTie(self):
    return self.type == self.TIE

  def isSymbol(self):
    return self.type == self.SYMB

  def hasLength(self):
    return self.length >= 0

  def hasProbability(self):
    return self.probability >= 0

  def leftTie(self):
    self.leftTies += 0.5

  def rightTie(self):
    self.rightTies += 0.5


class Onset(Symbol):

  def __init__(self, on):
    self.on = on
    super(Onset, self).__init__(type=Symbol.ONSET)


class Tie(Symbol):

  def __init__(self):
    super(Tie, self).__init__(type=Symbol.TIE)

class Grid(object):

  ON = 0
  OFF = 1

  def __init__(self, levels):
    self.levels = levels
  
  @staticmethod
  def division(depth):
    return 1/float(math.pow(2, depth))

  @staticmethod
  def getGrid(A, B, notes):
    levels = {}
    # If both symbols don't have a grid
    p = []
    for (note, beat, depth) in notes:
      if note.isOnset():
        p.append((note.on, depth))
      else:
        p.append(('tie', depth))

    if not A.hasGrid() and not B.hasGrid():
      length = 0.0
      started = False
      start = end = 0
      for (note, beat, depth) in notes:
        if not started:
          if note.isOnset():
            start = note.on
            started = True
            length += 1/float(math.pow(2, depth))
        elif note.isOnset():
          end = note.on
          break
        else:
          length += 1/float(math.pow(2, depth))
      # Is this correct?
      if started and end:
        levels[(0, )] = 1/float(length) * (end - start)
        #print '-----------'
        #print p
        #print '-----------'
    # If one of them does
    elif A.hasGrid():
      levels[(0, )] = A.grid.levels[(0, )] * 2.0
      #for (key, value) in A.grid.levels.iteritems():
      #  levels[(key[0]+1, )] = value
    elif B.hasGrid():
      levels[(0, )] = B.grid.levels[(0, )] * 2.0
      #for (key, value) in B.grid.levels.iteritems():
      #  levels[(key[0]+1, )] = value
    # If both symbols have a grid
    else:
      levels[(0, )] = A.grid.levels[(0, )] + B.grid.levels[(0, )]
      #for (key, value) in A.grid.levels.iteritems() + B.grid.levels.iteritems():
      #  if (key[0]+1, ) in levels:
      #    # Tricky assumption
      #    levels[(key[0]+1, )] = 0.5 * levels[(key[0]+1,)] + 0.5 * value
      #  else:
      #    levels[(key[0]+1, )] = value
    if len(levels) > 0:
      return Grid(levels)
    return None

  def getLength(self, beat, level):
    if beat == self.ON:
      pass
    if beat == self.OFF:
      pass
    return self.levels[(0, )]/float(math.pow(2, level))

