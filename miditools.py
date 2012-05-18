import re, csv

data_file = 'instruments.csv'
data = []

def prog2instr(prog):
  if len(data) == 0:
    f = csv.reader(open(data_file, 'rb'))
    for (program, instr, perc, fam) in f:
      if program.isdigit():
        if perc is 'None':
          perc = None
        data.append((int(program), instr, perc, fam))

  for (program, instr, perc, fam) in data:
    if program == prog:
      return (instr, perc, fam)

    


  


