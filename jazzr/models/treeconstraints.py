from jazzr.corpus import annotations
from jazzr.tools import commandline
import os, math, pickle, re, random

def train(corpus):
    allowed_symbols = []
    for (annotation, parse) in corpus:
        for symbol in getSymbols(parse):
            if not symbol in allowed_symbols:
                allowed_symbols += [symbol]
    return allowed_symbols

def count_onsets(S):
    onsets = 0
    if S.isSymbol():
        for child in S.children:
            if child.isOnset():
                onsets += 1
            elif child.isSymbol():
                onsets += count_onsets(child)
    return onsets

def getSymbols(S):
    symbols = []
    if S.isSymbol():
        if count_onsets(S) == 1:
            # Temporary hack
            #symbols = [tree(S), otherTree(S)]
            symbols = [tree(S)]
        for child in S.children:
            for symbol in getSymbols(child):
                if not symbol in symbols:
                    symbols += [symbol]
    else:
        return []
    return symbols

# Temporary hack
def otherTree(S):
    types = ['on', 'tie', 'symb']
    if S.isTie() or S.isOnset():
        return types[S.type]
    if S.children[0].isTie() and S.children[1].isOnset():
        return ['tie', 'tie', 'on']
    return [otherTree(child) for child in S.children]

def tree(S):
    types = ['on', 'tie', 'symb']
    if S.isTie() or S.isOnset():
        return types[S.type]
    return [tree(child) for child in S.children]

def loglikelihood(S, model):
    logP = 0.0
    N = 0
    if S.isSymbol():
        N += 1
        rule = ruleType(S)
        logP += math.log(model[rule])
        for child in S.children:
            logp, n = loglikelihood(child, model)
            logP += logp
            N += n
    return logP, N

def cross_entropy(S, model):
    logP, N = loglikelihood(S, model)
    return - 1/float(N) * logP


def cross_validate(folds=5):
    corpus = annotations.corpus()
    n = len(corpus)
    results = []
    for i in range(folds):
        print 'Preparing fold {0} out of {1}'.format(i+1, folds)
        trainset = []
        testset = []
        n_test = int(n/float(folds))
        for j in range(n_test):
            index = int(random.random() * (n-j))
            testset += [corpus[index]]
            del corpus[index]
        trainset = corpus

        print 'Training model'
        model = train(trainset)
        print 'Done. Model: {0}'.format(model)
        print 'Evaluating model.'
        cross_ent = 0
        for (a, parse) in testset:
            logP, N = loglikelihood(parse, model)
            cross_ent += -logP
        cross_ent /= float(n_test)
        print 'Done. Average cross-entropy: {0}'.format(cross_ent)
        results.append(cross_ent)
        corpus = trainset + testset
    result = sum(results)/float(len(results))
    print 'All done. Resulting cross-entropy: {0}'.format(result)
