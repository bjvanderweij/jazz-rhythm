"""JazzR

A Library of midi tools and algorithms for analysing rhythm in jazz music
"""

class Annotation:

    # Some annotation types
    NOTE = 0
    REST = 1
    GRACE = 2
    ERROR = 3
    END = 4
    SWUNG = 5

    def __init__(self, annotation, notes, metadata):
        from jazzr.rhythm import meter
        self.annotation = annotation
        self.notes = notes
        self.metadata = metadata
        self.bpm = metadata['bpm']
        self.name = metadata['name']
        self.meter = meter.getMeter(metadata)
        # Onset units per second (1000000 = onsets in microseconds)
        self.scale = 1000000

    @staticmethod
    def getAnnotation((annotation, notes, metadata)):
        return Annotation(annotation, notes, metadata)

    def __iter__(self):
        return self.generateItems()

    def __len__(self):
        return len(self.annotation)

    def __contains__(self, annotation):
        for a in self.annotation:
            if a is annotation:
                return True
        return False

    def __getitem__(self, i):
        return self.annotation[i]

    def __setitem__(self, i, item):
        self.annotation[i] = item

    def generateItems(self):
        for a in self.annotation:
            yield a

    def position(self, index):
        """Return the position in in quarternotes of the annotation at the
        given index."""
        return self[index][0]

    def pitch(self, index):
        """Return the pitch of the note corresponding to the annotated at
        the given index."""
        return self[index][2]

    def type(self, index):
        """Return the type of the annotation at the given index."""
        return self[index][3]

    def onset(self, index):
        """Calculate the ideal onset of this position given the tempo in metadata"""
        beatlength = self.scale/(self.bpm/60.0)
        beats = self.position(index) / float(self.meter.quarters_per_beat())
        return beats * beatlength

    def offset(self, index, ignoreRests=False):
        """Calculate the ideal onset of this position given the tempo in metadata"""
        return self.onset(self.nextPosition(index, ignoreRests=ignoreRests))

    def onbeat(self, index):
        pass

    def offbeat(self, index):
        pass

    def perf_onset(self, index):
        """Return the onset of the note corresponding to the annotation at
        the given index."""
        return self.notes[self[index][1]][0]

    def perf_offset(self, index):
        """Return the offset of the note corresponding to the annotation at
        the given index."""
        return self.notes[self[index][1]][1]

    def velocity(self, index):
        """Return the velocity of the note corresponding to the annotation at
        the given index."""
        return self.notes[self[index][1]][2]

    def deviation(self, index):
        """Calculate the proportion of a beat that the given onset deviates
        from the ideal onset corresponding to the given position."""
        beatlength = self.scale/(self.bpm/60.0)
        beats = self.position(index) / float(self.meter.quarters_per_beat())
        beat_onset = beats * beatlength
        deviation = self.onset(index) - beat_onset
        return deviation / beatlength

    def quarterLength(self, index):
        """Return the quarter length of the item at index in annotations."""
        return self.nextPosition(index) - self.onset(index)

    def realLength(self, index):
        """Return the length in microseconds that is expected given the bpm..."""
        on = self.annotation[index][0]
        off = on + self.quarterLength(index)
        return onset(off) - onset(on)

    def ioi(self, index, ignoreRests=True):
        return self.onset(self.nextPosition(index, ignoreRests=ignoreRests)) - self.onset(index)

    def perf_ioi(self, index, ignoreRests=True):
        return self.perf_onset(self.nextPosition(index, ignoreRests=ignoreRests)) - self.perf_onset(index)

    def log_ioi_ratio(self, index, ignoreRests=True):
        return math.log(self.perf_ioi(index) /\
            float(self.ioi(index, ignoreRests=ignoreRests)))

    def log_length_ratio(self, index):
        pass

    def bar(self, position):
        """Return the bar in which this position occurs"""
        beats = position / float(self.meter.quarters_per_beat())
        return int(beats // self.meter.beatspb)

    def barposition(self, position):
        """Calculate the position in quarter notes relative to the
        beginning of the bar."""
        beats = position / float(self.meter.quarters_per_beat())
        return beats - self.meter.beatspb * (beats // self.meter.beatspb)

    def nextPosition(self, index, ignoreRests=False):
        if self.type(index) == self.GRACE: return 0
        if self.type(index) in (self.END, self.ERROR):
            print '[warning] {0} Tried to get next position from invalid note type, returning 0.'.format(self.name)
            return 0
        if index+1 == len(self):
            print '[warning] {0} Last item in annotation is not END marker.'.format(self.name)
            return 0
        next = -1
        for i in range(index+1, len(self)):
            if self.position(i) != self.position(index) and\
                (self.type(i) in (self.NOTE, self.END) and ignoreRests) or\
                (self.type(i) in (self.NOTE, self.REST, self.END and not ignoreRests)):
                next = i
                break
        if next == -1:
            print '[warning] {0} Could not determine onset of next item after {1}.'.format(self.name, index)
        return next

    def split(self, index):
        """Split notes and rests that span across multiple bars in separate
        (bound) notes and rests."""
        if not type in [self.REST, self.NOTE]:
            return [self[index]]
        ql = self.quarterLength(index)
        current = self.position(index)
        remainder = ql
        result = []
        barlength = self.meter.quarters_per_bar()
        while self.bar(current) < self.bar(current + remainder):
            diff = (self.bar(current)+1)*barlength - current
            result.append((current, self[index][1], self.pitch(index), self.type(index)))
            remainder -= diff
            current += diff
        if remainder > 0:
            result.append((current, self[index][1], self.pitch(index), self.type(index)))
        return result

    def midi2name(self, pitch):
        from jazzr.midi import representation
        return representation.Note(0, 0, pitch, 0).name()

    def realbook(self, stdscr=None):
        from jazzr.tools import rbsearch
        from jazzr.corpus import midi
        name = self.name.split('-')[0]
        index = rbsearch.load_file()
        hits = rbsearch.find(index, name.replace('_', ' '))
        if len(hits) > 0:
            (song, book) = rbsearch.choose_book(index, hits, stdscr=stdscr)
            rbsearch.view(song, book)

    def transcribe(self, transpose=0):
        from music21 import stream, clef, tempo, meter, note, duration, metadata
        """Return a music21 score object, generated from the annotations"""
        score = stream.Score()
        score.metadata = metadata.Metadata()
        score.metadata.title = self.name
        score.metadata.composer = ''
        part = stream.Part()
        measurecount = self.bar(self.position(-1))
        if measurecount == 0: return
        for i in range(int(measurecount)):
            part.insert(stream.Measure())
        part[0].insert(0, clef.TrebleClef())
        part[0].insert(0, tempo.MetronomeMark(self.bpm))
        part[0].insert(0, meter.TimeSignature('{0}/{1}'.format(int(self.meter.beatspb), int(self.meter.beatdiv))))
        if 'key' in self.metadata:
            part[0].insert(0, key.KeySignature(self.metadata['key']))

        barsplit = []
        for i in range(len(self)):
            barsplit += self.split(i)

        temp = self.annotation
        self.annotation = barsplit

        for i in range(len(self)):
            (position, index, pitch, type) = self[i]
            measure = self.bar(position)
            measurepos = self.barposition(position)

            if type in [self.NOTE, self.REST, self.GRACE]:
                quarterLength = self.quarterLength(i)
                if quarterLength < 0: continue
                n = note.Note()
                n.midi = pitch + transpose
                n.duration = duration.Duration(quarterLength)
                if type == self.GRACE:
                    n = n.getGrace()
                if type == self.REST:
                    n = note.Rest(quarterLength)
                part[measure].insert(measurepos, n)

        score.insert(part)
        self.annotation = temp
        return score
