from jazzr.tools import latex, transcription
from jazzr.midi import representation
from jazzr.annotation import Annotation
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
  def fill(onsets, division):
    beats = [None for x in range(division)]
    for pos, onset in onsets:
      if int(pos) == pos and pos < division:
        beats[int(pos)] = onset
    if len(onsets) <= 1:
      return beats
    
    for (p1, t1), (p2, t2) in zip(onsets[:-1], onsets[1:]):
      if p2 - p1 == 0:
        length = 0
      else:
        length = (t2 - t1)/float(p2 - p1)
      for i in range(0, int(p2)):
        if beats[i] == None:
          beats[i] = t1 + (i - p1) * length
    if division > int(p2):
      for i in range(int(p2), division):
        if beats[i] == None:
          beats[i] = t1 + (i - p1) * length
    return beats

  @staticmethod
  def fromSymbols(Symbols, corpus=False):
    # beats should be filled with actual onsets, and filled with onsets estimated from those
    # as soon as two onsets are defined, upper symbols only add their own onsets
    division = len(Symbols)
    positions = []
    onsets = [None for x in range(division)]
    complexpositions = []

    previous = None
    next = None

    perf_complexpositions = []
    perf_positions = []
    perf_on = None

    if corpus:
      if len(Symbols) == 3 and Symbols[0].isTie() and Symbols[1].isTie():
        if Symbols[2].annotation.type(Symbols[2].index) == Annotation.SWUNG and not Symbols[2].annotation.position(Symbols[2].index) - int(Symbols[2].annotation.position(Symbols[2].index)) == 0:
          positions.append((0, int(Symbols[2].on)))
    #      perf_positions.append((0, Symbols[2].annotation.perf_onset(Symbols[2].index) - 2/3.0 * 60000000/float(Symbols[2].annotation.bpm)))

    for S, pos in zip(Symbols, range(0, division)):
      if S.isOnset():
        positions.append((pos, S.on))
        onsets[pos] = S
        if previous == None:
          previous = S.previous
        next = S.next
        if corpus:
          perf_positions.append((pos, S.annotation.perf_onset(S.index)))

      elif S.isSymbol():
        (complexpos, (p, onset, n)) = S.features
        next = n
        if previous == None:
          previous = p

        if S.beats[0] != None:
          positions.append((pos, S.beats[0]))
          if S.onsets[0] != None:
            onsets[pos] = S.onsets[0]
        else:
          complexpositions.append((pos + complexpos, onset))
        if S.beats[1] != None and S.beats[0] != None:
          positions.append((pos+1, S.beats[0] + len(S.children) * (S.beats[1] - S.beats[0])))

        if corpus:
          perf_complexpos, perf_on = S.perf_on
          if S.perf_beats[0] != None:
            perf_positions.append((pos, S.perf_beats[0]))
          else:
            perf_complexpositions.append((pos + perf_complexpos, perf_on))
          if S.perf_beats[1] != None and S.perf_beats[0] != None:
            perf_positions.append((pos+1, S.perf_beats[0] + len(S.children) * (S.perf_beats[1] - S.perf_beats[0])))
  
    length = None
    if len(positions) <= 1:
      positions += complexpositions
    position, onset = positions[0]
    features = (position/float(division), (previous, onset, next))

    positions = sorted(positions, key=lambda x:x[0])
    beats = Symbol.fill(positions, division)
    if len(positions) >= 2:
      length = division * (beats[1] - beats[0])

    perf_beats = None
    if corpus:
      if len(perf_positions) <= 1:
        perf_positions += perf_complexpositions
      position, on = perf_positions[0]
      perf_on = (position/float(division), on)
      perf_positions = sorted(perf_positions, key=lambda x:x[0])
      perf_beats = Symbol.fill(perf_positions, division)

    children = Symbols
    divisions = max([S.divisions for S in Symbols], key=lambda x: len(x))[:]
    divisions.append(len(Symbols))
    depth = max([S.depth for S in Symbols]) + 1
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

  def latex(self, showOnsets=False, showPerfOnsets=False, showRatios=False, showFeatures=False):
    return latex.latexify(self, showOnsets=showOnsets, showPerfOnsets=showPerfOnsets, showRatios=showRatios)

  def view(self, scale=False, showOnsets=False, showPerfOnsets=False, showRatios=False, showFeatures=False, quiet=True):
    """Generate a LaTeX tree using qtree.sty, convert to pdf with pdflatex and view using Evince. Remove the files afterwards."""
    latex.view_symbols([self], scale=scale, showOnsets=showOnsets, showPerfOnsets=showPerfOnsets, showRatios=showRatios, showFeatures=showFeatures, quiet=quiet)

  def score(self, barlevel=0, annotation=None):
    """Transcribe the symbol, save as MusicXML, convert to pdf using MuseScore and view using Evince. Remove the file afterwards."""
    transcription.view_pdf(self, barlevel=barlevel, annotation=annotation)

  def musescore(self, barlevel=0, annotation=None, filename='transcription'):
    transcription.musescore(self, barlevel=barlevel, annotation=annotation)

  def __str__(self):
    types = ['Onset', 'Tie', 'Symbol']
    info = ''
    if self.type == self.SYMB:
      return '[{0}:\tLength {1} Features {2} Depth {3}]'.format(types[self.type], self.length, self.features, self.depth)
    else:
      return '[{0}]'.format(types[self.type])

  def fromString():
    # To be implemented
    pass

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

