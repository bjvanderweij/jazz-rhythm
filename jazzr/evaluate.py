from jazzr.rhythm.parsers import *
from jazzr.models import *
import random, pickle

def evaluate(nfolds = 5, n=15, measures=2):
  corpus = annotations.corpus('explicitswing')

  folds = getFolds(corpus, folds=nfolds)
  results = []
  i = 1
  for trainset, testset in folds:
    print 'Fold {0}'.format(i)
    i += 1
    alpha = 0.0
    std = 0.15
    beam = 0.01    
    #std, alpha, beam = expression.train(trainset)
    model = pcfg.train(trainset)
    allowed = treeconstraints.train(trainset)
    parser = StochasticParser(n=n, std=std, expected_logratio=alpha, model=model, allowed=allowed, beam=beam)
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
        precision, recall = downbeat_detection(parses[0], label)  
        print precision, recall
      else:
        print 'Some test didn\'t return any results'
  f = open('results/std={0}_beam={1}_n={2}_folds={3}_measures={4}'.format(std, beam, n, nfolds, measures), 'wb')
  pickle.dump(results, f)
  return results

def measure(results):
  precision = 0.0
  recall = 0.0
  n = 0
  for parse, label in results:
    p, r = downbeat_detection(parses[0], label)
    precision += p
    recall += r
    n += 1
  return precision/float(n), recall/float(n), (precision+recall)/float(precision*recall)


def getTests(testset, measures=2):
  tests = []
  labels = []
  for test, label in testset:
    onsets = []
    bar = None
    for i in range(len(test)):
      if test.type(i) in [Annotation.NOTE, Annotation.END, Annotation.SWUNG]:
        onsets.append(test.perf_onset(i))
        if bar == None:
          bar = test.bar(test.position(i))
        else:
          if test.bar(test.position(i)) > bar + measures:
            break
    tests.append(onsets)
    labels.append(label)
  return tests, labels

ONSET = 0
TIE = 1

def symbol_to_list(S, level=0, beat=0, ties=False):
  treelist = []
  if S.isSymbol():
    for child, beat in zip(S.children, range(len(S.children))):
      treelist += symbol_to_list(child, level=level+1, beat=beat, ties=ties)
  elif S.isOnset():
    treelist.append((ONSET, beat, level))
  elif S.isTie() and ties:
    treelist.append((TIE, beat, level))
  return treelist

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
    type, beat, level = results[i]
    ltype, lbeat, llevel = labels[i]
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
  return precision, recall

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
