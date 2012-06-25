from jazzr.rhythm import grid, meter
from jazzr.annotation import Annotation
import math

def met_pos(annotation, index):
  metric_pos = annotation.barposition(annotation.position(index)) * 2
  if metric_pos in range(8):
    return metric_pos
  return -1

def loglikelihood(annotation, data):
  (name, model) = data
  if name == 'hierarchical':
    pass
  elif name == 'metrical_position':
    pass

  probability = 1.0
  n = 0
  for i in range(len(annotation)):
    if annotation.type(i) == Annotation.NOTE:
      p = met_pos(annotation, i)
      if p != -1:
        probability += math.log(model[int(p)])
        n += 1
  if n == 0:
    return 0
  return -probability / float(n)


def metrical_position(annotations):
  # Count metrical positions of notes
  # Ignore triplets for now
  met_positions = [0 for i in range(8)]
  bars = 0
  for annotation in annotations:
    if len(annotation) > 0:
      bars += annotation.bar(annotation.position(-1))
    for i in range(len(annotation)):
      if annotation.type(i) == Annotation.NOTE:
        p = met_pos(annotation, i)
        if p != -1:
          met_positions[int(p)] += 1
  model = [met_positions[i]/float(bars) for i in range(8)]
  return ('metrical_position', model)

  
def hierarchical(annotations):
  # Assume four levels
  # Ignore triplets for now
  # Count notes in each level
  # Count un, pre, post, both in each level
  levels = []
  for annotation in annotations:
    l = count_levels(annotation)
    levels = [levels[i] + l[i] for i in range(len(levels))]

  model = {}
  return ('hierarchical', model)

def count_levels(annotation):
  levels = []
  for i in range(len(annotation)):
    if annotation.type(i) == Annotation.NOTE:
      levels[grid.level(position)]

