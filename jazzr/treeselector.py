#!/usr/bin/python
from jazzr.rhythm import groupingparser as gp
from jazzr.corpus import annotations
from jazzr.tools import commandline, rbsearch
import math, os, pickle, re

directory = os.listdir('.')[commandline.menu('', os.listdir('.'))]
files = os.listdir(directory)

standard = re.compile('([a-z_]+-[0-9]+-[0-9]+)-[0-9]+')
standards = {}
for f in files:
  m = standard.match(f)
  if m:
    name = m.group(0)
    if not name in standards:
      standards[name] = m.group(1)


for s in standards.keys():
  parses = []
  exp = re.compile('{0}-parse_([0-9])+.pdf'.format(s))
  pdffiles = []
  print s
  for f in files:
    m = exp.match(f)
    if m:
      pdffiles.append((int(m.group(1)), m.group(0)))
  pdffiles = sorted(pdffiles, key=lambda x: x[0])
  print '{0} parses found.'.format(len(pdffiles))
  for (part, pdf) in pdffiles:
    print 'Loading score'
    index = rbsearch.load_file()
    hits = rbsearch.find(index, s.split('-')[0].replace('_', ' '))
    if len(hits) > 0:
      (song, book) = rbsearch.choose_book(index, hits)
      rbsearch.view(song, book)
    print 'Showing parsetree'
    os.system('evince "{0}/{1}"'.format(directory, pdf))
    if raw_input('Correct parse? (y/n) ') == 'y':
      path = '{0}/{1}-parse_{2}'.format(directory, s, part)
      command = 'cp "{0}" "../Data/corpus/annotated/annotations/{1}/{2}-parse.pickle"'.format(path, standards[s], s)
      os.system(command)
      break


