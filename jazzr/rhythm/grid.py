

class Grid:

  DOWN = 0
  UP = 1

  ONSET=0
  TIE=1
  

  def __init__(self):
    self.levels = {}
    self.beats = []
    pass

  def addTie(self, level, beat):
    self.beats.append((level, beat, self.TIE))

  def addBeat(self, level, beat, onset):
    self.levels[(level, beat)] = onset
    self.beats.append((level, beat, self.ONSET))

  def combine(self, grids):
    for grid in grids:
      for beat in grid.beats:
        self.beats.append(beat)
      for level, onset in grid.levels.iteritems():
        if not level in self.levels:
          self.levels[level] = onset
    levels = sorted(self.levels.keys(), key=lambda x: x[0])
    maxlevel = levels[0]

    newbeats = []
    for level, beat, type in self.beats:
      newbeats.append((level+1, beat, type))
    self.beats = newbeats

  def getOnset(self, position):
    pass

class Level:

  def __init__(self, downbeats=[], upbeats=[]):
    self.downbeats = downbeats
    self.upbeats = upbeats
    self.ratio=ratio

  def ratio(self):
    pass

class MetricUnit:

  def __init__(self, down=None, up=None, children=[]):
    self.down = down
    self.up = up

  def getDownBeat():
    if isinstance(self.down, MetricUnit):
      return self.down.getDownBeat():
    else:
      return self.down






