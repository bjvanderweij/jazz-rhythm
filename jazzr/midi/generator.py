from jazzr.midi import representation
from jazzr.rhythm import meter
import math

def annotations2midi(notes, meter=meter.Meter(4, 4), bpm=120, velocity=80, swing=2/3.0):
    mid = representation.MidiFile()
    mid.setbpm(bpm)
    mid.time_signature = (meter.beatspb, meter.beatdiv, 24, 8)
    tactuslength = mid.quarternotes_to_ticks(meter.quarters_per_beat())
    notes = sorted(notes, key=lambda x: x[0])
    mid['0'] = representation.Track(mid, 1)
    for i in range(len(notes)):
        (quarter, pitch, type) = notes[i]
        beat = quarter / meter.quarters_per_beat()
        if type == 1: continue
        length = tactuslength
        if i + 1< len(notes):
            length = (notes[i+1][0] - beat)*tactuslength
        on = beat*tactuslength
        off = on+length
        mid['0'].notes.append(representation.Note(on, off, pitch, velocity))
    return mid
