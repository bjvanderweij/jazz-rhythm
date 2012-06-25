from jazzr.annotation import Annotation
import math

# A subdivision based approach (like Longuet-Higgins, extended with probabilities)

maxdepth = 5

def rules(position, metadata):
  """Determine the subdivision rules that have been applied to get from
  a whole note to this note."""
  pass

def train(corpus):
  result = {}
  for annotation in corpus:
    for i in range(len(annotation)):
      barpos = annotation.barposition(annotation[i][0]) / 4.0
      sd = subdivide(barpos)
      if not sd:
        continue
      result[sd] = result.get(sd, []) + \
          [annotation.deviation(i)]

  for key, value in result.iteritems():
    result[key] = sum([abs(x) for x in value]) / float(len(value))
    print '{0}: {1}\t{2} examples'.format(key, result[key], len(value))
  return result



def parse(annotation):
  subdivisions = {}
  for i in range(len(annotation)):
    position = annotation.position(i)
    barpos = annotation.barposition(position) / 4.0
    print '({2}) Bar {0},{1}. '.format(annotation.bar(position), annotation.barposition(position), position),
    sd = subdivide(barpos)
    if not sd:
      print 'Not found'
      continue
    print '{2},{0}: {1}'.format(sd, annotation.deviation(i), barpos/explicit(sd))
    subdivisions[sd] = subdivisions.get(sd, []) + \
        [annotation.deviation(i)]
    

def subdivide(beat, division=0, depth=0, position=0):
  if not division:
    division = wholebeat()
  if depth == maxdepth: return 0
  if begin(division, beat):
    return tuple(division)
  if not interruption(division, beat):
    beat = subtract(division, beat)
    return subdivide(beat, division=division, depth=depth, position=position+1)
  duple = subdivide(beat, division=divide(division, 2),\
      depth=depth+1, position=position)
  triple = subdivide(beat, division=divide(division, 3),\
      depth=depth+1, position=position)
  if duple and triple:
    if len(triple) < len(duple):
      return triple
    return duple
  elif duple: return duple
  else: return triple




def wholebeat():
  return [1]

def divide(division, n):
  return division + [n]

def explicit(division):
  if len(division) == 0: return 1
  r = division[0]
  for n in division:
    r /= float(n) 
  return r

def begin(division, beat):
  if division[-1] == 2: return equals(beat, 0)
  if division[-1] == 3: return equals(beat, 0) or equals(beat, explicit(division))
  return equals(beat, 0)

def interruption(division, beat):
  rbound = (division[-1]-1) * explicit(division)
  if division[-1] == 1:
    rbound = explicit(division)
  return greater(beat, 0) and smaller(beat, rbound)

def subtract(division, beat):
  return beat - explicit(division)

def equals(a, b, precision=6):
  return int(round(a * math.pow(10, precision))) == int(round(b * math.pow(10, precision)))

def smaller(a, b, precision=6):
  return int(round(a * math.pow(10, precision))) < int(round(b * math.pow(10, precision)))

def greater(a, b, precision=6):
  return int(round(a * math.pow(10, precision))) > int(round(b * math.pow(10, precision)))




