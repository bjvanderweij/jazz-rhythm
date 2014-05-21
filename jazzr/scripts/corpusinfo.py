from jazzr.corpus import annotations
import re

corpus = annotations.corpus()

notes = 0
rests = 0
end_markers = 0
songs = 0
versions = 0
parts = 0
graces = 0
ignored = 0

songs = []
exp = re.compile('\w+')
for annotation, parse in corpus:
    parts += 1
    name = exp.match(annotation.name).group(0)
    print name
    if not name in songs:
        songs.append(name)
    for i in range(len(annotation)):
        if annotation.type(i) in [annotation.NOTE, annotation.SWUNG]:
            notes += 1
        elif annotation.type(i) == annotation.END:
            end_markers += 1
        elif annotation.type(i) == annotation.REST:
            rests += 1
        elif annotation.type(i) == annotation.GRACE:
            graces += 1
        elif annotation.type(i) == annotation.ERROR:
            ignored += 1

print '{0} notes, {1} rests, {2} end markers, {3} ignored notes, {4} grace notes. {5} songs, {6} parts'.format(notes, rests, end_markers, ignored, graces, len(songs), parts)
