#!/usr/bin/python

from jazzr.rhythm import groupingparser as gp
from jazzr.corpus import annotations
import math, os, pickle

def latexify(S, depth=0):
  res = ''
  if S.isOnset():
    res += '[ .$\\bullet$ ] '
  elif S.isTie():
    res += '[ .$*$ ] '
  if S.isSymbol():
    res += '[ .$\\frac{{1}}{{{0}}}$ '.format(int(math.pow(2, depth)))
    for child in S.children:
      res += latexify(child, depth=depth+1)
    res += '] '
  return res

def latexify_list(L, depth=0):
  res = ''
  if L == 'on':
    res += '[ .$\\bullet$ ] '
  elif L == 'tie':
    res += '[ .$*$ ] '
  else:
    res += '[ .$\\frac{{1}}{{{0}}}$ '.format(int(math.pow(2, depth)))
    for child in L:
      res += latexify_list(child, depth=depth+1)
    res += '] '
  return res
  
def run():
  corpus = annotations.loadAll()
  import datetime
  time = str(datetime.datetime.now())
  os.mkdir(time)

  for annotation in corpus[20:]:
    print annotation.name
    if len(annotation) < 10:
      continue
    parses = gp.parse_annotation(annotation, verbose=False)
    if len(parses) == 0:
      print 'No parses :('
      continue
    results = []
    for parse in parses:
      results.append((parse.depth, parse))

    outTxt = open('{0}/{1}-parses.txt'.format(time, annotation.name), 'w')
    counter = 0
    minimumdepth = min(results, key=lambda x: x[0])[0]
    for result in sorted(results, key=lambda x: x[0]):
      if result[0] == minimumdepth:
        os.mkdir('{0}/temp/'.format(time))
        os.system('cp ../Report/qtree.sty "{0}/temp/"'.format(time))
        out = open('{0}/{1}-parse_{2}'.format(time, annotation.name, counter), 'wb')
        latex = open('{0}/temp/{1}-parse_{2}.tex'.format(time, annotation.name, counter), 'w')
        latex.write('\\documentclass[a4paper,10pt]{article}\n\\usepackage{qtree}\n\\usepackage{fullpage}\n\\usepackage{lscape}\n\\begin{document}\n')
        latex.write('\\begin{landscape}\n\\resizebox{\\linewidth}{!}{\n\\Tree\n')
        latex.write(latexify(result[1]))
        latex.write('}\n\\end{landscape}\n\\end{document}')
        latex.close()
        os.chdir('{0}/temp/'.format(time))
        os.system('pdflatex "{0}-parse_{1}.tex"'.format(annotation.name, counter))
        os.system('cp "{0}-parse_{1}.pdf" ../'.format(annotation.name, counter))
        os.chdir('../../')
        os.system('rm -r "{0}/temp"'.format(time))
        pickle.dump(result[1], out)
        out.close()
        counter += 1
      outTxt.write('{0}:{1}\n'.format(result[0], gp.tree(result[1])))

    outTxt.close()


if __name__ == '__main__':
  run()
  

