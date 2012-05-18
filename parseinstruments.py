import re


def fam(m, families):
  families.append((int(m.group(1)), int(m.group(2)), m.group(3).rstrip()))
  families.append((int(m.group(4)), int(m.group(5)), m.group(6).rstrip()))

def inst(m, instruments):
  instruments.append((int(m.group(1)), m.group(2).rstrip()))
  instruments.append((int(m.group(3)), m.group(4).rstrip()))

def perc(m, percussion_list):
  percussion_list.append((int(m.group(1)), m.group(2).rstrip()))


def parse():
  f = open('instruments.txt')

  family = re.compile('([0-9]+)-([0-9]+)\s+([a-zA-Z\s]+)([0-9]+)-([0-9]+)\s+([a-zA-Z\s]+)')
  instrument = re.compile('([0-9]+)\.\s+([a-zA-Z\s\(\)\-]+[0-9]*\s+)([0-9]+)\.\s+([a-zA-Z0-9\s]+)')
  percussion = re.compile('([0-9]+)\.\s+([\-a-zA-Z0-9\s]+)')

  families = []
  instruments = []
  percussion_list = []

  regexs = (family, instrument, percussion)
  funs = (fam, inst, perc)
  lists = (families, instruments, percussion_list)
  i = 0

  for line in f:
    if re.search('#Families', line):
      i = 0
    if re.search('#Instruments', line):
      i = 1
    if re.search('#Percussion', line):
      i = 2
    m = regexs[i].match(line)
    if m:
      funs[i](m, lists[i])

  selector = lambda x: x[0]
  return (sorted(families, key=selector), sorted(instruments, key=selector), sorted(percussion_list, key=selector))
 
def save():
  (families, instruments, percussion) = parse()
  out = open('instruments.csv', 'w')
  out.write('Program #, Instrument, Percussion, Family\n')
  for inst in instruments:
    program = inst[0]
    family = None
    perc = None
    for f in families:
      if f[0] <= program and f[1] >= program:
        family = f[2]
    for p in percussion:
      if p[0] == program:
        perc = p[1]
    out.write('{0},{1},{2},{3}\n'.format(program, inst[1], perc, family))
  out.close()

