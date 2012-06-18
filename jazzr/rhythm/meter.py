class Meter:

  def __init__(self, beatspb, beatdiv):
    self.beatspb = beatspb
    self.beatdiv = beatdiv

  def quarters_per_beat(self):
    return (1/float(self.beatdiv)) /\
        (1/4.0)

  def quarters_per_bar(self):
    return self.quarters_per_beat() * self.beatspb

def getMeter(metadata):
  return Meter(metadata['beatspb'], metadata['beatdiv'])
