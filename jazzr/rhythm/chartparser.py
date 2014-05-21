from jazzr.rhythm import grammar
from jazzr.rhythm.grammar import NonTerminal, Terminal

class Span:

    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

class Onset:

    def __init__(self, onset, length, grammar):
        self.onset = onset
        self.length = length
        self.grammar = grammar


class Length:

    def __init__(self, length):
        self.length = length

class BeatSymbol:

    def __init__(self, division, formula):
        self.division = division
        self.formula = formula

    @staticmethod
    def generate(beats):
        if len(beats) == 1:
            pass

def combine(spanlist):
    i = 0
    reduced = []
    while True:
        if i >= len(spanlist):
            break
        if spanlist[i][0] == 'onset' and i+1 < len(spanlist):
            if spanlist[i+1][0] == 'onset':
                reduced += [('span', spanlist[i][1], spanlist[i][2], spanlist[i+1][2])]
                i += 1
            elif spanlist[i+1][0] == 'unit':
                spanlist[i] = ('onset', spanlist[i][1] + spanlist[i+1][1], spanlist[i][2])
                del spanlist[i+1]
            elif spanlist[i+1][0] == 'span':
                reduced += [('span', spanlist[i][1], spanlist[i][2], spanlist[i+1][2]), spanlist[i+1]]
                i += 2
        else:
            reduced += [spanlist[i]]
            i += 1
    return reduced

def probability(features, tolerance=0):
    # Integrity check:
    spans = []
    for item in features:
        if item[0] == 'span':
            spans.append((item[1], item[3]-item[2]))
    if len(spans) > 0:
        wholenote = 1/float(spans[0][0]) * spans[0][1]
    for (metrical, span) in spans:
        note = 1/float(metrical) * span
        if abs(note - wholenote) <= tolerance:
            wholenote = note
        else:
            return 0
    return 1

def musical_close(grammar, S, beam=0.5):
    cell = []
    unseen = []
    # Cell [Item0, Item1, ..., ItemN]
    # Item (Symbol, Features, Probability, Backpointer)
    while True:
        # Get the heads of the trees in S
        symbols = []
        features = []
        for x in S:
            symbols += [x.symbol]
            features += x.features
        symbols = tuple(symbols)
        if (symbols) in grammar:
            combined = combine(features)
            p = probability(combined)
            if p > beam:
                for production in grammar[symbols]:
                    unseen += [NonTerminal(production, S, combined, probability=p)]
        if unseen == []:
            break
        S = (unseen.pop(), )
        cell += S
    return cell

def generateSequences(Notes, depth):
    lengths = grammar.noteLengths(depth)
    for n in notes:
        for length in lengths:



def mcky(N, depth, beam=0.5, tiedNotes=False):
    if tiedNotes:
        generate_options(N)

def musical_cky(N, depth, beam=0.5, tiedNotes=False):
    g = grammar.generate(depth)

    n = len(N)
    t = {}
    # Iterate over rows
    for j in range(1, n+1):
        # Fill diagonal cells
        cell = grammar.onset_cell(N[j-1], depth)
        t[j-1, j] = tuple(cell)

        # Iterate over columns
        for i in range(j-2, -1, -1):
            cell = []

            for k in range(i+1, j):
                for B in t[i,k]:
                    for C in t[k,j]:
                        cell += musical_close(g, (B, C), beam=beam)
                        items = {}

            t[i,j] = tuple(cell)
    return t

def close(S, bp1=None, bp2=None):
    cell = []
    unseen = []
    while True:
        # Get the heads of the trees in S
        symbols = tuple([x[0] for x in S])
        if symbols in grammar.grammar:
            unseen += [(A, S) for A in grammar.grammar[symbols]]
        if unseen == []:
            break
        S = (unseen.pop(), )
        cell += [S]
    return cell

def cky(W):
    n = len(W)
    t = {}
    # Iterate over rows
    for j in range(1, n+1):
        # Fill diagonal cells
        S = ((W[j-1], ), )
        cell = close(S)
        t[j-1, j] = tuple(cell)

        # Iterate over columns
        for i in range(j-2, -1, -1):
            cell = []

            for k in range(i+1, j):
                for B in t[i,k]:
                    for C in t[k,j]:
                        cell += close((B+C))
            t[i,j] = tuple(cell)
    return t
