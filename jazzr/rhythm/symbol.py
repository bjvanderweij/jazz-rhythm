class Symbol(object):

  # Types
  ONSET = 0
  TIE = 1
  SYMB = 2
  SONG = 3
  
  #Beats
  ON = 0
  OFF = 1

  def __init__(self, features, length=None, children=None, depth=0, type=SYMB, grid=None):
    self.depth = depth
    self.type = type
    self.children = children
    self.length = length
    self.features = features

  @staticmethod
  def fromSymbols(Symbols):
    tiesLeft = 0.0
    tiesRight = 0.0
    previous = 0.0
    on = 0.0
    onsetDefined = False
    next = 0.0
    span = None
    childLength = 1/float(len(Symbols))

    for S in Symbols:
      if S.isTie():
        if onsetDefined:
          tiesRight += childLength
        else:
          tiesLeft += childLength
      elif S.isOnset():
        next = S.next
        if onsetDefined:
          span = (tiesRight, S.on - on)
          tiesRight += childLength
        else:
          onsetDefined = True
          previous = S.previous
          on = S.on
          tiesRight = childLength
      else:
        (tl, (p, o, n), tr) = S.features
        next = n
        if onsetDefined:
          tiesRight += tl * childLength
          span = (tiesRight, o - on)
          tiesRight += tr * childLength
        else:
          onsetDefined = True
          previous = p
          on = o
          tiesLeft += tl * childLength
          tiesRight = tr * childLength
          if S.hasLength():
            span = (childLength, S.length)

    features = (tiesLeft, (previous, on, next), tiesRight)
    length = None
    if span:
      length = 1/float(span[0]) * span[1]
    depth = max([S.depth for S in Symbols]) + 1
    children = Symbols
    R = Symbol(features, length=length, children=children, depth=depth)
    return R

  def hasLength(self):
    return self.length != None
  
  def isOnset(self):
    return self.type == self.ONSET

  def isTie(self):
    return self.type == self.TIE

  def isSymbol(self):
    return self.type == self.SYMB

  def isSong(self):
    return self.type == self.SONG

  def __str__(self):
    types = ['Onset', 'Tie', 'Symbol']
    info = ''
    if self.type == self.SYMB:
      return '[{0}:\tLength {1} Features {2}]'.format(types[self.type], self.length, self.features)
    else:
      return '[{0}]'.format(types[self.type])

class Onset(Symbol):

  def __init__(self, previous, on, next):
    self.previous = previous
    self.on = on
    self.next = next
    super(Onset, self).__init__([], type=Symbol.ONSET)

  def __str__(self):
    return '[{3}:\tOn {0}, Previous {1}, Next {2}]'.format(self.on, self.previous, self.next, super(Onset, self).__str__())

class Tie(Symbol):

  def __init__(self):
    super(Tie, self).__init__([], type=Symbol.TIE)

