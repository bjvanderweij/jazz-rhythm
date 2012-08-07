import os, datetime, math

qtree = '/home/bastiaan/Courses/Jazz-Rhythm/Report/qtree.sty'

def bottomlevel(S):
  if not S.isSymbol():
    return False
  for c in S.children:
    if not c.isOnset():
      return False
  return True


def latexify(S, depth=0, showOnsets=False, showPerfOnsets=False, showRatios=False, showFeatures=False):
  res = ''
  c = 0.000001
  if S.isOnset():
    if showPerfOnsets:
      res += '[ .${0:.3}$ ] '.format(S.annotation.perf_onset(S.index)*c)
    elif showOnsets:
      res += '[ .${0}$ ] '.format(S.on)
    else:
      res += '[ .$\\bullet$ ] '
  elif S.isTie():
    res += '[ .$*$ ] '
  if S.isSymbol():
    extras = []
    if showFeatures:
      if S.hasLength():
        extras.append('{0:.2}'.format(float(S.length)))
        extras.append('{0}'.format(S.beats))
        extras.append('{0}'.format(S.features))
    if showRatios:
      if S.hasDownbeat() and S.hasUpbeat() and bottomlevel(S.children[0]):
        l = S.upbeat - S.downbeat
        dbl = S.children[0].upbeat - S.children[0].downbeat
        upbl = l - dbl
        extras.append('{0:.2}'.format(dbl/float(upbl)))
        print 'begin: {0:.2} length: {1:.2}, down {2:.2} up {3:.2}, dbl:{4:.2} upbl:{5:.2}'.format(S.downbeat * c, l * c, S.children[0].downbeat * c, S.children[0].upbeat *c, dbl *c, upbl *c)
    res += '[ .{{$\\frac{{1}}{{{0}}}${1}}} '.format(int(math.pow(2, depth)), ','.join(extras))
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

def symbols_to_pdf(symbols, filename='parse', scale=True, showPerfOnsets=False, showOnsets=False, showRatios=False, showFeatures=False, quiet=True):
  time = str(datetime.datetime.now())
  os.mkdir('{0}/'.format(time))
  os.system('cp "{0}" "{1}/"'.format(qtree, time))
  latex = open('{0}/{1}.tex'.format(time, filename), 'w')
  body = ''
  for S in symbols:
    tree = '\Tree\n{0}\n\n'.format(latexify(S, showOnsets=showOnsets, showPerfOnsets=showPerfOnsets, showRatios=showRatios, showFeatures=showFeatures))
    if scale:
      tree = '\\begin{{landscape}}\n\\resizebox{{\\linewidth}}{{!}}{{\n{0}\n}}\n\\end{{landscape}}\n'.format(tree)
    body += tree
  #print create_document(body, packages=['qtree', 'fullpage', 'lscape'])
  latex.write(create_document(body, packages=['qtree', 'fullpage', 'lscape']))
  pipe = ''
  if quiet:
    pipe = '> /dev/null'
  latex.close()
  os.chdir('{0}/'.format(time))
  os.system('pdflatex "{0}.tex" {1}'.format(filename, pipe))
  os.system('cp "{0}.pdf" ../'.format(filename))
  os.chdir('../')
  os.system('rm -r "{0}/"'.format(time))

def view_symbols(symbols, scale=True, showOnsets=False, showPerfOnsets=False, showRatios=False, showFeatures=False, quiet=True):
  symbols_to_pdf(symbols, scale=scale, showPerfOnsets=showPerfOnsets, showOnsets=showOnsets, showRatios=showRatios, showFeatures=showFeatures, quiet=quiet)

  os.system('evince parse.pdf')
  os.system('rm parse.pdf')
