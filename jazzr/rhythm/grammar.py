def generate(depth):
  grammar = {}
  division = 1
  grammar[(1, 1)] = (1,)
  for i in range(depth):
    grammar[(division*2, division*2)] = (division,)
    # Only CNF rules are accepted by the parser
    grammar[(division*3, (division*3, division*3))] = (division,)
    grammar[(division*3, division*3)] = ((division*3, division*3), )
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


  


