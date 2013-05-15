from jazzr.rhythm.parsers import *
from jazzr.tools import commandline
from jazzr.corpus import annotations
import pickle, os

def select(results):
  name = sorted(results.keys())[commandline.menu('', sorted(results.keys()))]
  return results[name]

def save_most_likely(pickles, do=[]):
  for key in pickles:
    split = key.split('-')
    name = '-'.join(split[:-1])
    part = int(split[-1]) + 1
    if not name.split('-')[0] in do and len(do) > 0:
      continue
    annotations.save_parse('explicitswing', name, part, pickles[key][0])

def load_pickles():
  results = {}

  for name in os.listdir('output'):
    f = open('output/{0}'.format(name), 'rb')
    name, parse = pickle.load(f)
    results[name] = parse
  return results

def parse(parse = []):
  corpus, parser = SimpleParser.corpusAndParser()
  for song in corpus:
    if not song.name.split('-')[0] in parse and len(parse) > 0:
      continue
    print song.name
    parses = parser.parse_annotation(song)
    if len(parses) > 0:
      print 'Parses: {0}'.format(len(parses))
      f = open('output/{0}'.format(song.name), 'wb')
      pickle.dump((song.name, parses), f)
      f.close()
    else:
      print 'No parses'

if __name__ == '__main__':
  parse()
