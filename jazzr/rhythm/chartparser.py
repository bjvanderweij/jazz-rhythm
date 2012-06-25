

class Span:

  def __init__(self, begin, end):
    self.begin = begin
    self.end = end

class Onset:

  def __init__(self, onset, length, grammar):
    self.onset = onset
    self.length = length
    self.grammar = grammar


class Length:

  def __init__(self, length):
    self.length = length

class BeatSymbol:

  def __init__(self, division, formula):
    self.division = division
    self.formula = formula

  @staticmethod
  def generate(beats):
    if len(beats) == 1:
      pass

def reduce(spanlist):
  i = 0
  reduced = []
  while True:
    if i >= len(spanlist): 
      break
    if spanlist[i][0] == 'onset' and i+1 < len(spanlist):
      if spanlist[i+1][0] == 'onset':
        reduced += [('span', spanlist[i][1], spanlist[i][2], spanlist[i+1][2])] 
        i += 1
      elif spanlist[i+1][0] == 'unit':
        spanlist[i] = ('onset', spanlist[i][1] + spanlist[i+1][1], spanlist[i][2])
        del spanlist[i+1]
      elif spanlist[i+1][0] == 'span':
        reduced += [('span', spanlist[i][2], spanlist[i][2], spanlist[i+1][2]), spanlist[i+1]] 
        i += 2
    else:
      reduced += [spanlist[i]]
      i += 1
  return reduced

def musical_close(S, bp1=None, bp2=None):
  cell = []
  unseen = []
  while True:
    # Get the heads of the trees in S
    symbols = tuple([x[0] for x in S])
    if symbols in grammar.grammar:
      unseen += [(A, S) for A in grammar.grammar[symbols]]
    if unseen == []:
      break
    S = (unseen.pop(), )
    cell += [S]
  return cell
  

def musical_cky(N):
  n = len(N)
  t = {}
  # Iterate over rows
  for j in range(1, n+1):
    # Fill diagonal cells
    S = grammar.onset_cell()
    cell = close(S)
    t[j-1, j] = tuple(cell)

    # Iterate over columns
    for i in range(j-2, -1, -1):
      cell = []

      for k in range(i+1, j):
        for B in t[i,k]:
          for C in t[k,j]:
            cell += close((B+C))
      t[i,j] = tuple(cell)
  return t
  
  

def close(S, bp1=None, bp2=None):
  cell = []
  unseen = []
  while True:
    # Get the heads of the trees in S
    symbols = tuple([x[0] for x in S])
    if symbols in grammar.grammar:
      unseen += [(A, S) for A in grammar.grammar[symbols]]
    if unseen == []:
      break
    S = (unseen.pop(), )
    cell += [S]
  return cell

def cky(W):
  n = len(W)
  t = {}
  # Iterate over rows
  for j in range(1, n+1):
    # Fill diagonal cells
    S = ((W[j-1], ), )
    cell = close(S)
    t[j-1, j] = tuple(cell)

    # Iterate over columns
    for i in range(j-2, -1, -1):
      cell = []

      for k in range(i+1, j):
        for B in t[i,k]:
          for C in t[k,j]:
            cell += close((B+C))
      t[i,j] = tuple(cell)
  return t
