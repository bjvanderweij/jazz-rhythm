from jazzr.rawmidi import *
import re, csv, sys

data_file = '../data/instruments.csv'
data = []

# Looks up midi instrument name associated with a program number
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

# Prints a midifile as text
def midi2text(f):
  stream = MidiInFile.MidiInFile(MidiToText.MidiToText(), open(f))
  stream.read()
  stream.close()
    


  


