from jazzr.rhythm import groupingparser as gp
from music21 import stream, clef, tempo, meter, note, duration, metadata

def transcribeTree(tree, barlevel=0):
    """Return a music21 score object, generated from a tree produced by the 
    grouping parser"""
    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = 'Transcription of rhythmic analysis'
    score.metadata.composer = ''
    part = stream.Part()
    part.insert(stream.Measure())
    part[0].insert(0, clef.TrebleClef())
    part[0].insert(0, meter.TimeSignature('4/4'))
    part = transcribe(tree, part, 0, barlevel=0)
    score.append(part)
    return score

def transcribe(S, score, level, barlevel=0, one=0):
  if not one:
    one = S[0]

  workingstream = score
  if level == barlevel:
    print 'Inserting bar'
    workingstream = stream.Measure()
  
  if S[2] == gp.IOI:
    print 'Inserting note'
    workingstream.append(note.Note(quarterLength=4* S[0]/float(one)))
  elif S[2] == gp.TIE:
    print 'Inserting tie'
    if len(workingstream) == 0:
      workingstream.append(note.Rest(quarterLength=4* S[0]/float(one)))
    else:
      workingstream[-1].quarterLength = 4*S[0]/float(one)
  elif S[2] == gp.SYMB:
    for child in S[1]:
      workingstream = transcribe(child, workingstream, level+1, barlevel=barlevel, one=one)
    if level == barlevel:
      score.append(workingstream)
      workingstream = score
  return workingstream


