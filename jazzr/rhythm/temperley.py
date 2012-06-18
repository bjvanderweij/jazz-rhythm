from jazzr.rhythm import grid, meter
import jazzr.annotation as types
import math

def met_pos(quarters, metadata, resolution=8):
  m = meter.getMeter(metadata)
  measurepos = quarters - (quarters // m.quarters_per_bar()) * 4
  metric_pos = (measurepos/4.0) * resolution
  if metric_pos in range(8):
    return metric_pos
  return -1

def loglikelihood(annotation, metadata, data):
  (name, model) = data
  if name == 'hierarchical':
    pass
  elif name == 'metrical_position':
    pass

  probability = 1.0
  n = 0
  for (position, index, pitch, type) in annotation:
    if type == types.NOTE:
      p = met_pos(position, metadata)
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
  for (annotation, notes, metadata) in annotations:
    m = meter.getMeter(metadata)
    if len(annotation) > 0:
      bars += int(annotation[-1][0] // m.quarters_per_bar())
    for (position, index, pitch, type) in annotation:
      if type == types.NOTE:
        p = met_pos(position, metadata)
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
  for (annotation, notes, metadata) in annotations:
    l = count_levels(annotations)
    levels = [levels[i] + l[i] for i in range(len(levels))]

  model = {}
  return ('hierarchical', model)

def count_levels(annotation):
  levels = []
  for (position, index, pitch, type) in annotation:
    if type == types.NOTE:
      levels[grid.level(position)]

