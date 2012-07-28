def train(corpus):
  pass
  
def getFeatures(S, downbeat=None, length=None, level=0):
  if downbeat == None and length==None:
    downbeat = S.perf_beats[0]
    length = S.perf_beats[1] - S.perf_beats[0]
  obs = []
  implied_beatLength = length / float(len(S.children))
  beatLength = implied_beatLength
  time = downbeat
  if S.hasLength():
    beatLength = S.perf_beats[1] - S.perf_beats[0]
    time = S.perf_beats[0]

  if S.children[0].isSymbol():
    newobs = getFeatures(S.children[0], downbeat, beatLength, level=level+1)
    obs += newobs
  elif S.children[0].isOnset():
    on = S.children[0].annotation.perf_onset(S.children[0].index)
    # Wait a sec, we don't care about downbeats. On the other hand, every downbeat is a upbeat
    #deviation = (on - downbeat)/float(implied_beatLength)
    #obs.append((level, deviation))

  time += implied_beatLength
  for child, beat in zip(S.children[1:], S.perf_beats[1:]):
    newobs.append((beat - time)/float(implied_beatLength))
    if child.isSymbol():

      newobs = getFeatures(child, time, beatLength, level=level+1)
      obs += newobs
    elif onset != None:
      on = onset.annotation.perf_onset(onset.index)
      deviation = (on - time)/float(implied_beatLength)
      obs.append((level, deviation))
    time += implied_beatLength
  return obs
