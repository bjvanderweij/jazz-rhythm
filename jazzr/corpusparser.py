#!/usr/bin/python

from jazzr.rhythm.parsers import *
from jazzr.corpus import annotations
import math, os, pickle

def run():
  corpus, parser = SimpleParser.corpusParser()
  corpus = annotations.loadAnnotations()
  import datetime
  time = str(datetime.datetime.now())
  os.mkdir(time)

  for annotation in corpus:
    parses = gp.parser.parse_onsets(corpus)
    if len(parses) == 0:
      print 'No parses :('
      continue
    parses


if __name__ == '__main__':
  run()
  

