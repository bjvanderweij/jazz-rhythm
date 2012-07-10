import math

maxdepth = 4

def preprocess(onsets):
  N = []
  lastonset = 0
  for a, b in zip(onsets[0:-1], onsets[1:]):
    N.append(Onset(lastonset, a, b))
    lastonset = a
    #N.append([b-a, None, IOI, None, 0])
  return N

def probability(S, verbose=False, corpus=True):
  threshold = 0
  if not S.hasGrid():
    if S.depth > maxdepth:
      return 0.0
    return 1.0
  # A hack to parse the corpus efficiently
  if S.grid.levels[(0, )] * 2.0 != int(S.grid.levels[(0, )] * 2) and S.grid.levels[(0, )] * 1.5 != int(S.grid.levels[(0, )] * 1.5):
    return 0.0
  start = 0
  anchored = False
  time = 0
  if verbose:
    print 'Expected unit length: {0}. Note list: '
    for (note, beat, div) in S.notes:
      if note.isOnset():
        print '{0} ({1}), '.format(note.on, Grid.getUnit(div)), 
      if note.isTie():
        print 'Tie ({0}), '.format(Grid.getUnit(div)), 
    print '\n',
  # Over complicated code to get an IOI from a series of notes and ties
  for (note, beat, div) in S.notes:
    if not anchored and note.isOnset():
      start = note.on - time
      next = note.next
      # If the previous notes started after the implicated start time this symbol is unlikely
      if note.previous - start > threshold:
        return 0.0
      if verbose:
        print 'Onset found. Start set to {0}'.format(start)
      anchored = True
    elif note.isOnset():
      next = note.next
      if verbose:
        print 'Onset found. Start set to {0}'.format(start)
      # If an onset doesn't occur at the time previous intervals suggest it to occur, this symbol is unlikely
      if abs(note.on - (start+time)) > threshold:
        return 0.0
    time += S.grid.getLength(beat, div)  
    if verbose:
      print time
  # If so many ties are added that the total length passes the next onset this symbol is unlikely
  if start+time - next > threshold:
    return 0.0
  for level in S.grid.levels.keys():
    pass
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
      print 'Filling ({0}, {1}) '.format(i, j),
      cell = []
      for k in range(i+1, j):
        for B in t[i,k]:
          for C in t[k,j]:
            cell += close([B,C], beam=beam)
      t[i,j] = cell
      print '{0} hypotheses'.format(len(cell))
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

  def __init__(self, notes=[], children=None, depth=0, type=SYMB, grid=None):
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
      notesA = [(A, Symbol.ON, [2])]
    else:
      for note in A.notes:
        notesA += [(note[0], note[1], note[2] + [2])]

    if B.isOnset() or B.isTie():
      notesB = [(B, Symbol.OFF, [2])]
    else:
      for note in B.notes:
        notesB += [(note[0], note[1], note[2] + [2])]
    notes = notesA + notesB
    depth = max(A.depth, B.depth) + 1
    children = [A, B]
    R = Symbol(grid=Grid.getGrid(children, notes), notes=notes, children=children, depth=depth)
    return R

  @staticmethod
  def tripleFromSymbols(A, B):
    # Requires that symbol B is a duple division symbol
    notesA = []
    notesB = []
    # This labels the notes as on or off beats
    # (which is not a property of the note itself
    # but a result of the derivation)
    if A.isOnset() or A.isTie():
      notesA = [(A, Symbol.ON, [3])]
    else:
      for note in A.notes:
        notesA += [(note[0], note[1], note[2] + [3])]

    for note in B.notes:
      notesB += [(note[0], note[1], note[2][:-1] + [3])]
    notes = notesA + notesB
    depth = max(A.depth, B.depth) + 1
    children = [A] + B.children
    R = Symbol(grid=Grid.getGrid(children, notes), notes=notes, children=children, depth=depth)
    return R

  def hasGrid(self):
    return self.grid != None
  
  def isOnset(self):
    return self.type == self.ONSET

  def isTie(self):
    return self.type == self.TIE

  def isSymbol(self):
    return self.type == self.SYMB

  def isSong(self):
    return self.type == self.SONG

class Song(Symbol):

  def __init__(self, Symbols):
    grid = Grid.averageGrid(Symbols)
    depth = max([S.depth for S in Symbols])
    children = []
    notes = []
    for S in Symbols:
      if S.isSong():
        children += S.children
      else: children += [S]
      notes += S.notes
    super(Song, self).__init__(grid=grid, notes=notes, children=children, depth=depth, type=Symbol.SONG)
    

class Onset(Symbol):

  def __init__(self, previous, on, next):
    self.previous = previous
    self.on = on
    self.next = next
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
  def averageGrid(Symbols):
    levels = {}
    if len(Symbols) == 0:
      return levels
    for (key, value) in Symbols[0].grid.levels.iteritems():
      levels[(key[0], )] = value
    for symbol in Symbols[1:]:
      for (key, value) in symbol.grid.levels.iteritems():
        if (key[0], ) in levels:
          levels[(key[0], )] = 0.5 * levels[(key[0],)] + 0.5 * value
        else:
          levels[(key[0], )] = value
    return Grid(levels)

  @staticmethod
  def getGrid(Symbols, notes):
    levels = {}
    levelzeros = []
    for S in Symbols:
      if S.hasGrid():
        levelzeros.append(S.grid.levels[(0, )])
    if len(levelzeros) > 0:
      #levels[(0, )] = sum(levelzeros) * len(Symbols) / len(levelzeros) 
      # Assume the first interval
      levels[(0, )] = levelzeros[0] * len(Symbols) 
    else:
      # Find the first interval in the note list and use it to derive the length of this unit (the level-0 length)
      length = 0.0
      started = False
      start = end = 0
      for (note, beat, div) in notes:
        if not started:
          if note.isOnset():
            start = note.on
            started = True
            length += Grid.getUnit(div)
        elif note.isOnset():
          end = note.on
          break
        else:
          length += Grid.getUnit(div)
      if started and end:
        levels[(0, )] = 1/float(length) * (end - start)
    if len(levels) > 0:
      return Grid(levels)
    return None

  @staticmethod
  def getUnit(division):
    r = 1
    for d in division:
      r /= float(d)
    return r

  def getLength(self, beat, division):
    return self.levels[(0, )] * Grid.getUnit(division)
    #if beat == self.ON:
    #  pass
    #if beat == self.OFF:
    #  pass
    #return self.levels[(0, )]/float(math.pow(2, level))

if __name__ == '__main__':
  profile()
