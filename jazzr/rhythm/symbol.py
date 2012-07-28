from jazzr.tools import latex
from jazzr.midi import representation
from jazzr.annotation import Annotation
import math
import transcription

class Symbol(object):

  # Types
  ONSET = 0
  TIE = 1
  SYMB = 2
  SONG = 3
  
  #Beats
  DOWN = 0
  UP = 1

  def __init__(self, features, length=None, children=None, depth=0, type=SYMB, beats=[], onsets=[], divisions=[], perf_beats=[], perf_on=None):
    self.depth = depth
    self.type = type
    self.children = children
    self.length = length
    self.features = features
    self.beats = beats
    self.onsets = onsets
    self.prior = 1.0
    self.likelihood = None
    self.divisions = divisions
    self.perf_beats = perf_beats
    self.perf_on = perf_on

  @staticmethod
  def fromSymbols(Symbols, corpus=False):
    # First onset position
    position = 0.0
    previous = 0.0

    on = 0.0
    perf_on = 0.0
    onsetDefined = False

    next = 0.0
    span = None
    perf_span = None
    childLength = 1/float(len(Symbols))

    start = None
    perf_start = None
    beats = [None for x in Symbols]
    perf_beats = [None for x in Symbols]
    onsets = [None for x in Symbols]
    
    if corpus:
      if len(Symbols) == 3 and Symbols[0].isTie() and Symbols[1].isTie():
        if Symbols[2].annotation.type(Symbols[2].index) == Annotation.SWUNG and not Symbols[2].annotation.position(Symbols[2].index) - int(Symbols[2].annotation.position(Symbols[2].index)) == 0:
          onsetDefined = True
          on = int(Symbols[2].on)
          start = (0, on)
          beats[0] = on
          perf_on = Symbols[2].annotation.perf_onset(Symbols[2].index) - 2/3.0 * 60000000/float(Symbols[2].annotation.bpm)
          perf_start = (0, perf_on)

    for S, beat in zip(Symbols, range(len(Symbols))):
      currentposition = beat/float(len(Symbols))
      if S.isTie():
        if not onsetDefined:
          position = currentposition
      elif S.isOnset():
        next = S.next
        onsets[beat] = S

        # GRID
        beats[beat] = S.on
        if corpus:
          perf_beats[beat] = S.annotation.perf_onset(S.index)
        if start == None:
          start = (currentposition, beats[beat])
          if corpus:
            perf_start = (currentposition, perf_beats[beat])

        if onsetDefined:
          span = (currentposition - position, S.on - on)
          if corpus:
            perf_span = (currentposition - position, perf_beats[beat] - perf_on)
        else:
          onsetDefined = True
          position = currentposition
          previous = S.previous
          on = S.on
          if corpus:
            perf_on = perf_beats[beat]
      else:
        (pos, (p, o, n)) = S.features
        if corpus:
          perf_o = S.perf_on
        pos *= childLength
        next = n
        if S.onsets[0] != None:
          onsets[beat] = S.onsets[0]

        # GRID
        if S.hasDownbeat():
          beats[beat] = S.downbeat()
          o = S.downbeat()
          if corpus:
            perf_beats[beat] = S.perf_beats[0]
            perf_o = S.perf_beats[0]
        else:
          currentposition += pos
        if start == None:
          start = (currentposition, o)
          if corpus:
            perf_start = (currentposition, perf_o)

        if onsetDefined:
          span = (currentposition - position, o - on)
          if corpus:
            perf_span = (currentposition - position, perf_o - perf_on)
        else:
          onsetDefined = True
          previous = p
          on = o
          if corpus:
            perf_on = perf_o
          position = currentposition
          if S.hasLength():
            span = (childLength, S.length)
            if corpus:
              perf_span = (childLength, (S.perf_beats[1] - S.perf_beats[0]) * len(S.children))

    features = (position, (previous, on, next))

    length = None
    perf_length = None
    if span:
      length = 1/float(span[0]) * span[1]
      (position, on) = start
      if corpus:
        perf_length = 1/float(perf_span[0]) * perf_span[1]
        (position, performance_on) = perf_start
      for i in range(len(beats)):
        if beats[i] == None:
          beats[i] = on + (i/float(len(Symbols)) - position) * length
        if corpus:
          if perf_beats[i] == None:
            perf_beats[i] = performance_on + (i/float(len(Symbols)) - position) * perf_length

    divisions = max([S.divisions for S in Symbols], key=lambda x: len(x))[:]
    divisions.append(len(Symbols))
    depth = max([S.depth for S in Symbols]) + 1
    children = Symbols
    R = Symbol(features, length=length, children=children, depth=depth, beats=beats, onsets=onsets, divisions=divisions, perf_beats=perf_beats, perf_on=perf_on)
    return R

  def downbeat(self):
    return self.beats[0]

  def hasDownbeat(self):
    return self.beats[0] != None

  def hasLength(self):
    return self.length != None

  def hasLikelihood(self):
    return self.likelihood != None
  
  def isOnset(self):
    return self.type == self.ONSET

  def isTie(self):
    return self.type == self.TIE

  def isSymbol(self):
    return self.type == self.SYMB

  def tree(self):
    types = ['on', 'tie', 'symb']
    if self.isTie() or self.isOnset():
      return types[self.type]
    return [child.tree() for child in self.children]

  def transcribe(self, barlevel=0):
    if self.isSymbol():
      return transcription.transcribe(self, barlevel=barlevel)
    else:
      return None
  
  def midi(self, barlevel=0):
    transcription.save_midi(self, barlevel=barlevel)
    return representation.MidiFile('transcription.mid')
    os.system('rm transcription.mid')

  def view(self, scale=False):
    """Generate a LaTeX tree using qtree.sty, convert to pdf with pdflatex and view using Evince. Remove the files afterwards."""
    latex.view_symbols([self], scale=scale)

  def score(self, barlevel=0, annotation=None):
    """Transcribe the symbol, save as MusicXML, convert to pdf using MuseScore and view using Evince. Remove the file afterwards."""
    transcription.view_pdf(self, barlevel=barlevel, annotation=annotation)

  def __str__(self):
    types = ['Onset', 'Tie', 'Symbol']
    info = ''
    if self.type == self.SYMB:
      return '[{0}:\tLength {1} Features {2} Depth {3}]'.format(types[self.type], self.length, self.features, self.depth)
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

