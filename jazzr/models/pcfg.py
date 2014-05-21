from jazzr.corpus import annotations
from jazzr.tools import commandline
import os, math, pickle, re, random


def flat_prior(p=None):
    model = train(annotations.corpus())
    for key in model:
        model[key] = p
        if not p:
            model[key] = 1/float(len(model.keys()))
    return model

def train(corpus):
    counts = {}
    N = 0
    for (annotation, parse) in corpus:
        parsecounts = count_rules(parse)
        for (rule, count) in parsecounts.iteritems():
            counts[rule] = counts.get(rule, 0) + count
            N += count
    model = {}
    for (rule, count) in counts.iteritems():
        model[rule] = count/float(N)
        #print '{0}: {1}'.format(rule, count/float(N))
    # Some made up probabilities:
    #model[('on', 'tie', 'on')] = model['on', 'on'] / 3.0
    #model[('tie', 'on', 'on')] = model['on', 'on'] / 3.0

    #model[('tie', 'tie', 'on')] = model['tie', 'on'] / 2.0
#
    #model['on', 'on'] = model['on', 'on'] / 3.0
    #model['tie', 'on'] = model['tie', 'on'] / 2.0
    #model[(2, 2)] = 0.495
    #model[(3, 3)] = 0.495
    #model[(3, 2)] = 0.005
    #model[(2, 3)] = 0.005
    return model

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
        # This is needed because triple rules are constructed from a two duple CNF rules
        #if len(rule) == 3:
        #  counts[tuple(rule[1:])] = counts.get(tuple(rule[1:]), 0) + 1
        #  counts[tuple(rule[:1] + ('symb', ))] = counts.get(tuple(rule[:1] + ('symb', )), 0) + 1
        counts[tuple(rule)] = counts.get(tuple(rule), 0) + 1
        for child in S.children:
            childcounts = count_rules(child)
            for (r, count) in childcounts.iteritems():
                counts[r] = counts.get(r, 0) + count
    return counts

def probability(S, model, verbose=False):
    p = 1.0
    if S.isSymbol():
        # Time signature consistency
        #minl = len(min([child.divisions for child in S.children], key=lambda x: len(x)))
        #for i in range(minl):
        #  d = S.children[0].divisions[-i]
        #  for child in S.children[1:]:
        #    newd = child.divisions[-i]
        #    p *= model[(newd, d)]
        #    d = newd
        # PCFG
        rule = ruleType(S)
        if rule in model:
            p *= model[rule]
        else:
            p = 0
        for child in S.children:
            p *= probability(child, model)
    return p

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

def run():
    cross_validate(5)

    directory = os.listdir('.')[commandline.menu('', os.listdir('.'))]
    files = os.listdir(directory)

    standard = re.compile('([a-z_]+-[0-9]+-[0-9]+)-[0-9]+')
    standards = {}
    for f in files:
        m = standard.match(f)
        if m:
            name = m.group(0)
            if not name in standards:
                standards[name] = m.group(1)


    for s in standards.keys():
        parses = []
        exp = re.compile('{0}-parse_([0-9])+$'.format(s))
        print s
        for f in files:
            m = exp.match(f)
            if m:
                parses.append((int(m.group(1)), m.group(0)))
        parses = sorted(parses, key=lambda x: x[0])
        print '{0} parses found.'.format(len(parses))
        symbols = []
        results = []
        for (number, parse) in parses:
            S = pickle.load(open('{0}/{1}'.format(directory, parse)))
            p = probability(S, model)
            results.append((p, number))
            print 'Parse {0}: {1}'.format(number, p)
        if len(results) > 0:
            print 'Best parse: {0}'.format(max(results, key=lambda x: x[0]))
        while True:
            choice = -1
            if len(results) > 1:
                choice = commandline.menu('View tree?', [str(result[0]) for result in results])
            if choice == -1:
                break
            os.system('evince "{0}/{1}"'.format(directory, '{0}-parse_{1}.pdf'.format(s, results[choice][1])))
