from jazzr.annotation import data as datamod
from jazzr.corpus import midi
from jazzr.tools import commandline, rbsearch
from jazzr.midi import representation
import code

def annotate(path):
    midi = representation.MidiFile(path)
    (name, version, track, singletrack) = midi.parsename(midi.name)
    key = '{0}-{1}-{2}'.format(name, version, track)

    parts = ['percussion', 'bass', 'accompaniment', 'melody', None]
    part = None
    choice = -1

    index = rbsearch.load_file('data/realbooks/index.csv')
    hits = rbsearch.find(index, name.replace('_', ' '))

    score = 'No score found'
    if len(hits) > 0:
        score = 'Scores found'

    header = '>>> [{0}]\t[#{1}: {2}]\t[{3}]\t({4})'.format(name, track, midi['1'].name.strip(), midi['1'][1].instrument(), score)
    while choice not in [5, 6]:
        # Show options: play file,don't add to corpus
        choice = commandline.menu(header, ['Play file', 'Annotate', 'View info', 'Drop to shell', 'Search score', 'Save and next', 'Skip', 'Abort'])
        # Play file
        if choice == 0:
            midi['1'].play(gui=True)
        # Annotate
        elif choice == 1:

            part = parts[commandline.menu('Choose value for \'part\' attribute.', parts)]
        # View info
        elif choice == 2:
            print 'Name:\t\t{0}\nPath:\t\t{1}\nInstrument:\t{2}\n'.format(\
              midi.name, path, midi['1'][0].instrument())
        # Drop to shell
        elif choice == 3:
            code.interact(local=locals())
        elif choice == 4:
            if len(hits) == 0:
                print 'Sorry! No score found'
                if raw_input('Would you like to search manually? (y/n) ') == 'y':
                    query = raw_input('Search for: ')
                    hits2 = rbsearch.find(index, query)
                    if len(hits2) == 0:
                        print 'No results'
                        continue
                    (song, book) = rbsearch.choose_book(index, hits2)
                    rbsearch.view(song, book, 'data/realbooks/songs/')
                continue
            (song, book) = rbsearch.choose_book(index, hits)
            rbsearch.view(song, book, 'data/realbooks/songs/')
        # Abort
        elif choice == 7:
            if raw_input('Are you sure? (y/n) ') is 'y':
                exit(0)
    if choice == 5:
        return {'path':path, 'part':part}
    if choice == 6:
        return None




# This function assumes an inputdir containing single track midifiles
# The revise option toggles whether this will iterate over every file in
# inputdir or just the ones already in the datafile

# Some possibilities should include annotate everything that is [in inputdir], [in datafile AND inputdir]
# [in datafile], [in datafile but missing attribs], etc.
def simpleAnnotator(inputdir, datafile, revise=False, annotatefunction=annotate, saveEach=True):
    data = datamod.Data(datafile)
    if revise and 'path' in d.keys:
        paths = [item['path'] for item in data.values()]
    aset = midi.paths(inputdir)
    data.addAttrib('part')
    data.addAttrib('path')
    for f in aset:
        (name, version, track, singletrack) = midi.parsepath(f)
        key = '{0}-{1}-{2}'.format(name, version, track)
        annotation = annotatefunction(f)
        if annotation:
            for k in annotation.keys():
                if not k in data.keys:
                    data.addAttrib(k)
            data.add(key, annotation)
        if saveEach:
            data.save()

    if raw_input('Save to datafile? (y/n)') is 'y':
        data.save()
    else:
        backup = datafile + '.bak'
        data.save(backup)
        print 'A datafile of this session was stored in {0}'.format(backup)
