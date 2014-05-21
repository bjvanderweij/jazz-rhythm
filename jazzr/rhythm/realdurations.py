def getOnsets(S):
    if S.isSymbol():
        beats = []
        for child in S.children:
            beats += [tree2onsets(child)]
        return Duration(beats)
    elif S.isOnset():
        return Onset(S.annotation.perf_onset(S.index))
    else:
        return Tie()

def getDurations(S, duration):
    if S.isSymbol():
        if S.downbeat():

        for child in S.children:


class Duration(object):

    def __init__(self, beats):
        self.beats = beats

    def downbeat(self):
        return self.beats[0].downbeat()

    def upbeat(self, index=1):
        if index < len(self.beats):
            return self.beats[index].downbeat()
        return None

class Onset(Duration):

    def __init__(self, onset):
        self.onset = onset

    def downbeat(self):
        return self.onset

    def upbeat(self):
        return None

class Tie(Duration):

    def __init__(self):
        pass

    def downbeat(self):
        return None

    def upbeat(self):
        return None
