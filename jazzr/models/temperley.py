def train(corpus):
  counts = {}
  N = 0
  for (annotation, parse) in corpus:
    newcounts = getCounts(parse)
    for label, count in newcounts.iteritems():
      counts[label] = counts.get(label, 0) + count
      N += count
  model = {}
  for label, count in counts.iteritems():
    model[label] = count/float(N)
  return model

def getCounts(S, pre=False, post=False, post2=False, level=0):
  counts = {}
  if S.isSymbol():
    onsets = S.onsets
    downbeat = S.children[0]
    #Downbeat
    newcounts = getCounts(downbeat, pre=pre, post=post, post2=onsets[1] != None, level=level+1)
    for label, count in newcounts.iteritems():
      counts[label] = counts.get(label, 0) + count

    if len(S.children) == 2:
      upbeat = S.children[1]
      #Upbeat
      newcounts = getCounts(upbeat, pre=onsets[0] != None, post=post2, level=level+1)
      for label, count in newcounts.iteritems():
        counts[label] = counts.get(label, 0) + count
    elif len(S.children) == 3:
      upbeat1 = S.children[1]
      upbeat2 = S.children[2]
      #Upbeat
      newcounts = getCounts(upbeat1, pre=onsets[0] != None, post=post2, level=level+1)
      for label, count in newcounts.iteritems():
        counts[label] = counts.get(label, 0) + count
      newcounts = getCounts(upbeat2, pre=onsets[0] != None, post=post2, level=level+1)
      for label, count in newcounts.iteritems():
        counts[label] = counts.get(label, 0) + count
  elif S.isOnset():
    if pre and post:
      counts[level, 'both'] = counts.get((level, 'both'), 0) + 1
    elif pre and  not post:
      counts[level, 'pre'] = counts.get((level, 'pre'), 0) + 1
    elif not pre and post:
      counts[level, 'post'] = counts.get((level, 'post'), 0) + 1
    elif not pre and not post:
      counts[level, 'un'] = counts.get((level, 'un'), 0) + 1
  return counts


def ruleType(S):
  types = ['on', 'tie', 'symb']
  if not S.isSymbol(): return None
  rule = []
  for child in S.children:
    rule.append(types[child.type])
  return tuple(rule)

def count_rules(S):
  types = ['on', 'tie', 'symb']
  counts = {}
  if S.isSymbol():
    rule = ruleType(S)
    counts[tuple(rule)] = counts.get(tuple(rule), 0) + 1
    for child in S.children:
      childcounts = count_rules(child)
      for (r, count) in childcounts.iteritems():
        counts[r] = counts.get(r, 0) + count
  return counts
  
def probability(S, model):
  p = 1.0
  if S.isSymbol():
    # Time signature consistency
    minl = len(min([child.divisions for child in S.children], key=lambda x: len(x)))
    for i in range(minl):
      d = S.children[0].divisions[-i]
      for child in S.children[1:]:
        newd = child.divisions[-i]
        p *= model[(newd, d)]
        d = newd
    # PCFG
    rule = ruleType(S)
    if rule in model:
      p *= model[rule]
    else:
      p = 0
    for child in S.children:
      p *= probability(child, model)
  return p
