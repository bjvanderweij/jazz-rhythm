import os, datetime, math

qtree = '/home/bastiaan/Courses/Jazz-Rhythm/Report/qtree.sty'

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

def symbols_to_pdf(symbols, filename='parse', scale=True):
  time = str(datetime.datetime.now())
  os.mkdir('{0}/'.format(time))
  os.system('cp "{0}" "{1}/"'.format(qtree, time))
  latex = open('{0}/{1}.tex'.format(time, filename), 'w')
  body = ''
  for S in symbols:
    tree = '\Tree\n{0}\n'.format(latexify(S))
    if scale:
      tree = '\\begin{{landscape}}\n\\resizebox{{\\linewidth}}{{!}}{{\n{0}}}\n\\end{{landscape}}\n'.format(tree)
    body += tree
  latex.write(create_document(body, packages=['qtree', 'fullpage', 'lscape']))
  latex.close()
  os.chdir('{0}/'.format(time))
  os.system('pdflatex "{0}.tex"'.format(filename))
  os.system('cp "{0}.pdf" ../'.format(filename))
  os.chdir('../')
  os.system('rm -r "{0}/"'.format(time))

def view_symbols(symbols, scale=True):
  symbols_to_pdf(symbols, scale=scale)
  os.system('evince parse.pdf')
  os.system('rm parse.pdf')
