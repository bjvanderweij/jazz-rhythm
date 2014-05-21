from jazzr.annotation import convert
import jazzr.annotation as types
from music21 import *

def transcribe(annotation, metadata, transpose=0):
    # Construct a score from the notes in the annotation
    score = stream.Score()
    part = stream.Part()
    measurecount = convert.bar(annotation[-1][0], metadata)
    if measurecount == 0: return
    for i in range(int(measurecount)):
        part.insert(stream.Measure())
    part[0].insert(0, clef.TrebleClef())
    part[0].insert(0, tempo.MetronomeMark(metadata['bpm']))
    part[0].insert(0, meter.TimeSignature('{0}/{1}'.format(int(metadata['beatspb']), int(metadata['beatdiv']))))
    if 'key' in metadata:
        part[0].insert(0, key.KeySignature(metadata['key']))

    barsplit = []
    for i in range(len(annotation)):
        barsplit += convert.split(annotation, i, metadata)

    for i in range(len(barsplit)):
        (position, index, pitch, type) = barsplit[i]
        measure = convert.bar(position, metadata)
        measurepos = convert.barposition(position, metadata)

        if type in [types.NOTE, types.REST, types.GRACE]:
            quarterLength = convert.quarterLength(barsplit, i, metadata)
            if quarterLength < 0: continue
            n = note.Note()
            n.midi = pitch + transpose
            n.duration = duration.Duration(quarterLength)
            if type == types.GRACE:
                n = n.getGrace()
            if type == types.REST:
                n = note.Rest(quarterLength)
            part[measure].insert(measurepos, n)

    score.insert(part)
    score.show()
