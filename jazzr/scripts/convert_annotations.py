from jazzr.annotation import Annotation
from jazzr.corpus import annotations as acorpus

def convert(annotations):
  for i in range(len(annotations)):
    if annotations.type(i) == Annotation.NOTE:
      if annotations.position(i) - int(annotations.position(i)) == 0.5 and annotations.type(i) == Annotation.NOTE:
        if annotations.position(i-1) == int(annotations.position(i)) and annotations.type(i-1) == Annotation.NOTE:
          (beat, pos, pitch, type) = annotations[i-1]
          annotations[i-1] = (beat, pos, pitch, Annotation.SWUNG)
        (beat, pos, pitch, type) = annotations[i]
        annotations[i] = (int(beat)+2/3.0, pos, pitch, Annotation.SWUNG)
  return annotations


def run():
  corpus = acorpus.corpus()
  for (a, p) in corpus:
    print a.name
    newA = convert(a)
    normalname = '-'.join(newA.name.split('-')[:-1])
    part = newA.name.split('-')[-1:][0]
    newA.metadata['name'] = normalname
    newA.name = normalname
    acorpus.save_annotation('explicitswing', newA, midifile=acorpus.load_midifile('annotations', normalname), part=part)

run()
