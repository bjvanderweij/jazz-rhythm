def timesignatures():
  return ['4/4', '2/4', '3/4', '3/8', '6/8', '12/8', '2/2']


def add(grammar, symbols, production):
  grammar[symbols] = grammar.get(symbols, []) + [production]

def generate(depth):
  grammar = {}
  division = 1
  # Time signatures:
  add(grammar, (2, 2), '4/4')
  add(grammar, ('4/4', '4/4'), '4/4')

  add(grammar, (2, 4), '3/4')
  add(grammar, (4, 2), '3/4')
  add(grammar, ('3/4', '3/4'), '3/4')

  add(grammar, (4, 4), '2/4')
  add(grammar, (2), '2/4')
  add(grammar, ('2/4', '2/4'), '2/4')
  for i in range(depth):
    add(grammar, (division*2, division*2), division)
    # Only CNF rules are accepted by the parser
    add(grammar, (division*3, (division*3, division*3)), division)
    add(grammar, (division*3, division*3), (division*3, division*3))
    division *= 2
  return grammar

def onset_cell(onset, depth):
  # Problem: triplets can't have tied notes as it is now
  # A symbol: ((Cell), Semantics/Features)
  Cell = []
  division = 1
  Cell.append(Terminal(1, Terminal.NOTE, [('onset', 1, onset)]))
  for i in range(depth):
    duple = division * 2
    metrical = 1/float(duple)
    note = Terminal(duple, Terminal.NOTE, [('onset', metrical, onset)])
    Cell.append(note)

    triple = division * 3
    metrical = 1/float(triple)
    Cell.append(Terminal(triple, Terminal.NOTE, [('onset', metrical, onset)]))
    division *= 2
  return Cell


class Symbol(object):
  
  # Symbols: 1/x, 1/xN, 4 4, 3 4, 2 4, etc.

  def __init__(self, symbol, features, probability=1):
    self.symbol = symbol
    self.features = features
    self.probability = probability

  def getTree(self):
    return str(self.symbol)

  def metrical(self):
    if isinstance(self.symbol, int):
      return 1/float(self.symbol)
    return -1


class Terminal(Symbol):

  # Types: Note, Tied note
  NOTE = 0
  TIED = 1

  def __init__(self, symbol, type, features):
    self.type = type
    super(Terminal, self).__init__(symbol, features)

  def isNote(self):
    return self.type == self.NOTE

  def isTied(self):
    return self.type == self.TIED

  def getTree(self):
    if self.isTied():
      return '*'
    elif self.isNote():
      return str(self.symbol)

class NonTerminal(Symbol):

  def __init__(self, symbol, children, features, probability=1):
    self.children = children
    super(NonTerminal, self).__init__(symbol, features, probability=probability)

  def getTree(self):
    return '[{0}({1}), [{2}]]'.format(self.symbol, self.childrenSignature(), ', '.join([symbol.getTree() for symbol in self.children]))

  def childrenSignature(self):
    signature = ''
    for child in self.children:
      if isinstance(child, Terminal):
        if child.isNote():
          signature += 'n'
        elif child.isTied():
          signature += 'b'
      elif isinstance(child, NonTerminal):
        signature += 's'
    return signature


