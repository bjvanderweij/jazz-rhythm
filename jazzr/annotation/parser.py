import re

def parse_met_grid(infile):
    f = open(infile)
    stream = ''

    # Treat the file as a big stream of letters, ignore whitespaces, ignore comments
    for line in infile:
        if not line.startswith('#'):
            stream.append(line.split())

    exp = re.compile('(B)|([a-g]([#b])?[1-8][1248(16)])')

    buf = ''
    for char in stream:
        buf.append(char)
        if re.match(buf, exp):


    pass

def parse_notes(infile):
    pass
