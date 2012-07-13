import os, datetime, math

qtree = '/home/bastiaan/Courses/Jazz-Rhythm/Report/qtree.sty'

def latexify(S, depth=0, showOnsets=False, showRatios=False, showFeatures=False):
  res = ''
  if S.isOnset():
    if showOnsets:
      if S.annotation != None:
        res += '[ .${0}$ ] '.format(S.annotation.onset(S.index))
      else:
        res += '[ .${0}$ ] '.format(S.on)
    else:
      res += '[ .$\\bullet$ ] '
  elif S.isTie():
    res += '[ .$*$ ] '
  if S.isSymbol():
    extras = []
    if showFeatures:
      if S.hasBeatLength():
        extras.append('D={0}'.format(S.beatLength))
      if S.hasDownbeat():
        extras.append('down={0}'.format(S.downbeat))
        if S.hasBeatLength() and S.hasUpbeat():
          extras.append('down_l={0}'.format(S.upbeat-S.downbeat, S.downbeatLength()))
      if S.hasUpbeat():
        extras.append('up={0}'.format(S.upbeat))
        if S.hasBeatLength() and S.hasDownbeat():
          extras.append('up_l={0}'.format(S.upbeatLength()))
    if S.logRatio() != None and showRatios:
      extras.append('{0}'.format(math.exp(S.logRatio())))
    res += '[ .{{$\\frac{{1}}{{{0}}}$({1})}} '.format(int(math.pow(2, depth)), ','.join(extras))
    for child in S.children:
      res += latexify(child, depth=depth+1, showOnsets=showOnsets, showRatios=showRatios, showFeatures=showFeatures)
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

def create_document(body, packages=[], title=None, author=None):
  f = '\\documentclass[a4paper,10pt]{article}\n'
  if title:
    f += '\\title{{{0}}}\n'.format(title)
    if author:
      f += '\\author{{{0}}}\n'.format(author)
  for package in packages:
    f += '\\usepackage{{{0}}}\n'.format(package)
  f += '\\begin{{document}}\n{0}\n\\end{{document}}\n'.format(body)
  return f

def symbols_to_pdf(symbols, filename='parse', scale=True, showOnsets=False, showRatios=False, showFeatures=False):
  time = str(datetime.datetime.now())
  os.mkdir('{0}/'.format(time))
  os.system('cp "{0}" "{1}/"'.format(qtree, time))
  latex = open('{0}/{1}.tex'.format(time, filename), 'w')
  body = ''
  for S in symbols:
    tree = '\Tree\n{0}\n\n'.format(latexify(S, showOnsets=showOnsets, showRatios=showRatios, showFeatures=showFeatures))
    if scale:
      tree = '\\begin{{landscape}}\n\\resizebox{{\\linewidth}}{{!}}{{\n{0}\n}}\n\\end{{landscape}}\n'.format(tree)
    body += tree
  print create_document(body, packages=['qtree', 'fullpage', 'lscape'])
  latex.write(create_document(body, packages=['qtree', 'fullpage', 'lscape']))
  latex.close()
  os.chdir('{0}/'.format(time))
  os.system('pdflatex "{0}.tex"'.format(filename))
  os.system('cp "{0}.pdf" ../'.format(filename))
  os.chdir('../')
  os.system('rm -r "{0}/"'.format(time))

def view_symbols(symbols, scale=True, showOnsets=False, showRatios=False, showFeatures=False):
  symbols_to_pdf(symbols, scale=scale, showOnsets=showOnsets, showRatios=showRatios, showFeatures=showFeatures)
  os.system('evince parse.pdf')
  os.system('rm parse.pdf')
