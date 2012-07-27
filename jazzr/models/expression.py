def train(corpus):
  pass
  
def getFeatures(S, downbeat, length, level=0):
  obs = []
  implied_beatLength = length / float(len(S.children))
  beatLength = implied_beatLength
  time = downbeat
  if S.hasLength():
    beatLength = S.length / float(len(S.beats))
    time = S.downbeat()

  if S.children[0].isSymbol():
    newobs = getFeatures(S.children[0], downbeat, beatLength, level=level+1)
    obs += newobs
  elif S.children[0].isOnset():
    on = S.children[0].annotation.perf_onset(S.children[0].index)
    deviation = (downbeat - on)/float(implied_beatLength)
    obs.append((level, deviation))

  time += implied_beatLength
  for child, onset in zip(S.children[1:], S.onsets[1:]):
    if child.isSymbol():
      newobs = getFeatures(child, time, beatLength, level=level+1)
      obs += newobs
    elif onset != None:
      on = onset.annotation.perf_onset(onset.index)
      deviation = (time - on)/float(implied_beatLength)
      obs.append((level, deviation))
    time += implied_beatLength
  return obs
