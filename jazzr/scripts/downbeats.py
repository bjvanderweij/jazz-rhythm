DOWN=0
UP=1

def find(S, duration=1.0, beat=UP):
  onsets = {}
  durations = {}
  if S.isSymbol():
    beats = [ON] + [UP for i in range(len(S.children)-1)]
    for child in S.children:
      childDuration = duration/float(len(S.children))
      results = find(child, duration=childDuration, beat=beat)
      if results == None:
        if (childDuration,beat) in onsets:
          onsets[childDuration, beat] += childDuration
      elif isinstance(result, dict):
      else:
        if (childDuration,beat) in onsets:
          onsets[childDuration, beat] += [childDuration]
          durations[(childDuration, )] = result - onsets[childDuration, beat][0] * onsets[childDuration, beat][1:]
        else:
          onsets[childDuration, beat] = [results, childDuration]

  elif S.isOnset():
    return S.on
  elif S.isTie():
    return None
  return onsets
