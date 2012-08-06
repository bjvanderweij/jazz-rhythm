from jazzr.rhythm.parsers import *
from jazzr.models import *
from jazzr.tools import commandline
import random, pickle, datetime, os

def load():
  files = sorted(os.listdir('results'))
  choice = commandline.menu('Choose', files)
  if choice != -1:
    f = open('results/{0}'.format(files[choice]), 'rb')
    return pickle.load(f)

def evaluate(corpus, nfolds=10, n=15, measures=4, noise=False):
  folds = getFolds(corpus, folds=nfolds)
  results = []
  i = 1
  allowed = treeconstraints.train(corpus)
  for trainset, testset in folds:
    print 'Fold {0}'.format(i)
    i += 1
    
    # Train a parser
    if noise:
      parser = StochasticParser(trainset, n=n, expressionModel=expression.additive_noise(0.1))
      #parser.beam = 0.01
    else:
      parser = StochasticParser(trainset, n=n, expressionModel=expression.train(trainset))
      #parser.beam = 0.01
    parser.allowed = allowed
    # Get the first few bars from a piece
    tests, labels = getTests(testset, measures=measures)
    annot = [x[0] for x in testset]
    for test, label, annotation in zip(tests, labels, annot):
      print annotation.name
      if len(test) <= 2:
        print 'Skipping too short test'
        continue
      parses = parser.parse_onsets(test)
      if len(parses) > 0:
        results.append((parses[0], label))
        precision, recall = measure(results[-1:])
        print 'Precision {0} recall {1}.'.format(precision, recall)
        precision, recall = measure(results)
        print 'Averages: precision {0} recall {1}.'.format(precision, recall)
        
  time = str(datetime.datetime.now())
  type = 'expression'
  if noise:
    type = 'additive_noise'
  f = open('results/results_{0}_measures={1}_n={2}_folds={3}'.format(time, measures, n, nfolds), 'wb')
  pickle.dump(results, f)
  return results

def measure(results):
  recallScore = 0
  precisionScore = 0
  nRecall = 0
  nPrecision = 0
  for i in range(len(results)):
    parse, label = parseAndLabel(results, i)
    n, score = getPrecisionScore(parse, label)
    precisionScore += score
    nPrecision += n
    n, score = getRecallScore(parse, label)
    recallScore += score
    nRecall += n
  return precisionScore/float(nPrecision), recallScore/float(nRecall)

def precision(parse, label):
  tp, fp, tnl, fn = downbeat_detection(parse, label)
  precision = 0
  if tp + fp != 0:
    precision = tp/float(tp + fp)
  return precision

def recall(parse, label):
  tp, fp, tn, fn = downbeat_detection(parse, label)
  recall = 0
  if tp + fn != 0:
    recall = tp/float(tp + fn)
  return recall
  

def getTests(testset, measures=2):
  tests = []
  labels = []
  for test, label in testset:
    onsets = []
    bar = None
    for i in range(len(test)):
      if test.type(i) in [Annotation.NOTE, Annotation.END, Annotation.SWUNG]:
        if bar == None:
          bar = test.bar(test.position(i))
        else:
          if test.bar(test.position(i)) >= bar + measures:
            break
        onsets.append(test.perf_onset(i))
    tests.append(onsets)
    labels.append(label)
  return tests, labels

ONSET = 0
TIE = 1

def symbol_to_list(S, level=0, beat=0, ties=False, division=[1]):
  treelist = []
  if S.isSymbol():
    for child, beat in zip(S.children, range(len(S.children))):
      treelist += symbol_to_list(child, level=level+1, beat=beat, ties=ties, division=division+[len(S.children)])
  elif S.isOnset():
    treelist.append((ONSET, beat, level, division))
  elif S.isTie() and ties:
    treelist.append((TIE, beat, level, division))
  return treelist

      


def getFolds(corpus, folds=5):
  n = len(corpus)
  results = []
  for i in range(folds):
    trainset = []
    testset = []
    n_test = int(n/float(folds))
    for j in range(n_test):
      index = int(random.random() * (n-j))
      testset += [corpus[index]]
      del corpus[index]
    trainset = corpus
    results.append((trainset, testset))
    corpus = trainset + testset
  return results

def parseAndLabel(results, i):
  p = results[i][0]
  notes = getOnsets(p)
  return p, getSubTree(notes, results[i][1])

def compare(results, i, scale=False):
  p, l = parseAndLabel(results, i)
  latex.view_symbols([p, l], scale=scale)

def getSubTree(notes, parse):
  if parse.isSymbol():
    childContains = False
    for child in parse.children:
      if contains(notes, getOnsets(child, performance=True)):
        childContains = True
        res = getSubTree(notes, child)
        if res != None:
          return res
      if not childContains:
        return parse
  return None

def getOnsets(S, performance=False):
  notes = []
  if S.isSymbol():
    for child in S.children:
      notes += getOnsets(child, performance=performance)
  elif S.isOnset():
    if performance:
      return [S.annotation.perf_onset(S.index)]
    else:
      return [S.on]
  return notes

def contains(small, big):
  for i in xrange(len(big)-len(small)+1):
    for j in xrange(len(small)):
      if big[i+j] != small[j]:
        break
      else:
        return i, i+len(small)
  return False

def downbeat_detection(parse, correctparse):
  results = symbol_to_list(parse)
  labels = symbol_to_list(correctparse)
  n = 0
  tp = 0
  fp = 0
  tn = 0
  fn = 0
  #for i in range(len(results)):
  #  print results[i], labels[i]
  for i in range(len(results)):
    type, beat, level, division = results[i]
    ltype, lbeat, llevel, division = labels[i]
    if type == ONSET and beat == 0:
      if beat == lbeat:
        tp += 1
      else:
        fp += 1 
    elif type == ONSET:
      if lbeat != 0:
        tn += 1
      else:
        fn += 1 
  precision = recall = 0
  if tp + fp != 0:
    precision = tp/float(tp + fp)
  if tp + fn != 0:
    recall = tp/float(tp + fn)
  return tp, fp, tn, fn

def getPrecisionScore(parse, label, a_perf=False, b_perf=True, verbose=False):
  if verbose:
    if label == None:
      label = Tie()
    latex.view_symbols([parse, label], scale=False)
  score = 0
  n = 0
  # If this is a symbol than this symbol is one fact claimed by the parse
  # it's correct if the onsets each of its children governs is the same as for the parse
  division = len(parse.children)
  i = 0
  while i < division:
    n += 1
    if label == None:
      if parse.children[i].isSymbol():
        newN, newScore = getPrecisionScore(parse.children[i], None, a_perf=a_perf, b_perf=b_perf, verbose=verbose)
        n += newN
        score += newScore
      i += 1
      continue
    if label.children == None:
      if parse.children[i].isSymbol():
        newN, newScore = getPrecisionScore(parse.children[i], None, a_perf=a_perf, b_perf=b_perf, verbose=verbose)
        n += newN
        score += newScore
      i += 1
      continue
    if i >= len(label.children):
      if parse.children[i].isSymbol():
        newN, newScore = getPrecisionScore(parse.children[i], None, a_perf=a_perf, b_perf=b_perf, verbose=verbose)
        n += newN
        score += newScore
      i += 1
      continue
    # Parse claims a division into x and y, see if label does so too
    if getOnsets(parse.children[i], performance=a_perf) == getOnsets(label.children[i], performance=b_perf): 
      score += 1
      if parse.children[i].isSymbol():
        newN, newScore = getPrecisionScore(parse.children[i], label.children[i], a_perf=a_perf, b_perf=b_perf, verbose=verbose)
        n += newN
        score += newScore
    else:
      # Only do this at top level?
      #if contains(getOnsets(label, performance=b_perf), getOnsets(parse.children[i], performance=a_perf)):
      #  if parse.children[i].isSymbol():
      #    newN, newScore = getPrecisionScore(parse.children[i], label, a_perf=a_perf, b_perf=b_perf, verbose=verbose)
      #    n += newN
      #    score += newScore
      if contains(getOnsets(label.children[i], performance=b_perf), getOnsets(parse.children[i], performance=a_perf)):
        if parse.children[i].isSymbol():
          newN, newScore = getPrecisionScore(parse.children[i], label.children[i], a_perf=a_perf, b_perf=b_perf, verbose=verbose)
          n += newN
          score += newScore
      else:
        if parse.children[i].isSymbol():
          newN, newScore = getPrecisionScore(parse.children[i], None, a_perf=a_perf, b_perf=b_perf, verbose=verbose)
          n += newN
          score += newScore
    i += 1
  return n, score

def getRecallScore(parse, label, verbose=False):
  return getPrecisionScore(label, parse, a_perf=True, b_perf=False, verbose=verbose)

