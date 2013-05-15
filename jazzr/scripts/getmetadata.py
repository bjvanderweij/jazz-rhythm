from jazzr.corpus import midi, annotations

corpus = annotations.corpus()
names = []

for annotation, tree in corpus:
  name = '-'.join(annotation.name.split('-')[0:2])
  if not name in names:
    names.append(name)

for name in names:
  song, version, track, singletrack = midi.parsename(name)
  mf = midi.load(song, version, track, singletrack, collection='original')
  print mf.name
  for track in sorted(mf.keys()):
    print '\t{0}'.format(mf[track].name)
