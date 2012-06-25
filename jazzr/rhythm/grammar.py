def generate(depth):
  grammar = {}
  symbols = []
  division = 1
  symbols.append('1/{0}'.format(division))
  for i in range(depth):
    nextdivision = '1/{0}'.format(division * 3)
    symbols.append(nextdivision)
    grammar[(nextdivision, nextdivision, nextdivision)] = '1/{0}'.format(division)

    nextdivision = '1/{0}'.format(division * 2)
    symbols.append(nextdivision)
    grammar[(nextdivision, nextdivision)] = '1/{0}'.format(division)
    division *= 2
  return (grammar, symbols)

def onset_cell(onset, symbols):
  # A symbol: ((Cell), Semantics/Features)
  Cell = []
  for symbol in symbols:
    Cell.append(((symbol, ), [('onset', symbol, onset), ]))
    Cell.append(((symbol, symbol), [('onset', symbol, onset), ('unit', symbol)]))
    Cell.append(((symbol, symbol), [('unit', symbol), ('onset', symbol, onset)]))
    Cell.append(((symbol, symbol, symbol), [('unit', symbol), ('onset', symbol, onset), ('onset', symbol, onset)]))
    Cell.append(((symbol, symbol, symbol), [('onset', symbol, onset), ('unit', symbol), ('onset', symbol, onset)]))
    Cell.append(((symbol, symbol, symbol), [('onset', symbol, onset), ('onset', symbol, onset), ('unit', symbol)]))
    Cell.append(((symbol, symbol, symbol), [('unit', symbol), ('onset', symbol, onset), ('unit', symbol)]))
    Cell.append(((symbol, symbol, symbol), [('unit', symbol), ('unit', symbol), ('onset', symbol, onset)]))
  return Cell


  


