from jazzr.corpus import annotations
import re

corpus = annotations.corpus()

notes = 0
rests = 0
end_markers = 0
songs = 0
versions = 0
parts = 0



for annotation, parse in corpus:

