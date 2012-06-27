def timesignatures():
  return [('4/4', ), ('2/4', ), ('3/4', ), ('3/8', ), ('6/8', ), ('12/8', ), ('2/2', )]


def add(grammar, symbols, production):
  grammar[symbols] = grammar.get(symbols, []) + [production]

def generate(depth):
  grammar = {}
  division = 1
  # Time signatures:
  #add(grammar, (1, ), ('4/4', ))
  add(grammar, (2, 2), ('4/4', ))
  add(grammar, ('4/4', '4/4'), ('4/4', ))

  add(grammar, (2, 4), ('3/4', ))
  add(grammar, (4, 2), ('3/4', ))
  add(grammar, ('3/4', '3/4'), ('3/4', ))

  add(grammar, (4, 4), ('2/4', ))
  add(grammar, (2), ('2/4', ))
  add(grammar, ('2/4', '2/4'), ('2/4', ))
  for i in range(depth):
    add(grammar, (division*2, division*2), (division,))
    # Only CNF rules are accepted by the parser
    add(grammar, (division*3, (division*3, division*3)), (division,))
    add(grammar, (division*3, division*3), ((division*3, division*3), ))
    division *= 2
  return grammar

def onset_cell(onset, depth):
  # Problem: triplets can't have bound notes as it is now
  # A symbol: ((Cell), Semantics/Features)
  Cell = []
  division = 1
  Cell.append(((1, ), [('onset', 1, onset), ]))
  for i in range(depth):
    duple = division * 2
    metrical = 1/float(duple)
    Cell.append(((duple, ), [('onset', metrical, onset)]))
    Cell.append(((division, ), [('onset', metrical, onset), ('unit', metrical)]))
    Cell.append(((division, ), [('unit', metrical), ('onset', metrical, onset)]))

    triple = division * 3
    metrical = 1/float(triple)
    Cell.append(((triple, ), [('onset', metrical, onset)]))
    division *= 2
  return Cell


class Symbol:
  
  # Symbols: 1/x, 1/xN, 4 4, 3 4, 2 4, etc.

  def __init__(self, symbol, features, probability=1):
    self.symbol = symbol
    self.features = features
    self.probability = probability

class Terminal(Symbol):

  # Types: Note, Bound note

  def __init__(self, symbol, type, features):
    self.type = type
    Symbol(self, symbol, features)

class NonTerminal(Symbol):

  def __init__(self, symbol, children, features, probability=1):
    self.children = children
    Symbol(self, symbol, features, probability=probability)

