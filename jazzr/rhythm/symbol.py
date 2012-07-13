import math

class Symbol(object):

  # Types
  ONSET = 0
  TIE = 1
  SYMB = 2
  SONG = 3
  
  #Beats
  DOWN = 0
  UP = 1

  def __init__(self, features, length=None, children=None, depth=0, type=SYMB, downbeat=None, upbeat=None, beatLength=None):
    self.depth = depth
    self.type = type
    self.children = children
    self.length = length
    self.features = features
    self.downbeat = downbeat
    self.upbeat = upbeat
    self.beatLength = beatLength

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

    downbeat = None
    upbeat = None

    beatLength = None
    reference = 0
    beatpos = 0
    beatLengthDefined = False

    if len(Symbols) == 2:
      beats = [Symbol.DOWN, Symbol.UP]
    elif len(Symbols) == 3:
      beats = [Symbol.DOWN, Symbol.UP, Symbol.UP]

    for S, beat in zip(Symbols, range(len(Symbols))):
      if S.isTie():
        if onsetDefined:
          tiesRight += childLength
        else:
          tiesLeft += childLength
      elif S.isOnset():
        next = S.next

        # GRID
        if beats[beat] == Symbol.DOWN:
          if S.annotation != None:
            downbeat = S.annotation.onset(S.index)
          else:
            downbeat = S.on
        elif beats[beat] == Symbol.UP:
          if S.annotation != None:
            upbeat = S.annotation.onset(S.index)
          else:
            upbeat = S.on

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

        # GRID
        next = n
        if S.hasBeatLength() and not beatLengthDefined:
          beatlength = S.beatLength
          reference = S.downbeat
          beatpos = beat
          beatLengthDefined = True
        if S.hasDownbeat():
          if beats[beat] == Symbol.DOWN:
            downbeat = S.downbeat
          elif beats[beat] == Symbol.UP:
            upbeat = S.downbeat
        elif S.hasUpbeat():
          pass

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

    if downbeat != None and upbeat != None:
      Symbols[0].setBeatLength(upbeat-downbeat)
    if beatLengthDefined:
      for pos in range(len(Symbols)):
        if not S.hasDownbeat:
          S.setDownbeat(reference + (pos - beatpos) * beatlength)

    features = (tiesLeft, (previous, on, next), tiesRight)
    length = None
    if span:
      length = 1/float(span[0]) * span[1]
    depth = max([S.depth for S in Symbols]) + 1
    children = Symbols
    R = Symbol(features, length=length, children=children, depth=depth, upbeat=upbeat, downbeat=downbeat)
    return R

  def setDownbeat(self, downbeat):
    self.downbeat = downbeat
    if self.hasChildren():
      self.children[0].setDownbeat(downbeat)

  def setUpbeat(self, upbeat):
    self.upbeat = upbeat
    if self.hasChildren():
      self.children[1].setDownbeat(upbeat)

  def setBeatLength(self, beatLength):
    self.beatLength = beatLength

  def downbeatLength(self):
    if self.hasDownbeat() and self.hasUpbeat():
      return self.upbeat - self.downbeat
    return None

  def upbeatLength(self):
    if self.hasBeatLength() and self.hasDownbeat() and self.hasUpbeat():
      return self.beatLength - self.downbeatLength()
    return None

  def logRatio(self):
    if self.hasBeatLength() and self.hasDownbeat() and self.hasUpbeat():
      return math.log(self.downbeatLength()/float(self.upbeatLength()))
    return None

  def hasBeatLength(self):
    return self.beatLength != None

  def hasUpbeat(self):
    return self.upbeat != None

  def hasDownbeat(self):
    return self.downbeat != None

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

  def __init__(self, previous, on, next, annotation=None, index=None):
    self.previous = previous
    self.on = on
    self.next = next
    self.annotation = annotation
    self.index = index
    super(Onset, self).__init__([], type=Symbol.ONSET)

  def __str__(self):
    return '[{3}:\tOn {0}, Previous {1}, Next {2}]'.format(self.on, self.previous, self.next, super(Onset, self).__str__())

class Tie(Symbol):

  def __init__(self):
    super(Tie, self).__init__([], type=Symbol.TIE)

