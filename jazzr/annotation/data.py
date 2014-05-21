import csv, os

class Data:

    # Key,Part,Style,Path

    def __init__(self, datafile):
        self.data = {}
        self.datafile = datafile
        self.keys = []
        self.load()
        pass

    def load(self, datafile=None):
        if not datafile: datafile = self.datafile
        if not os.path.exists(datafile):
            print 'No data file found, {0} will be created when Data.save() is called.'.format(datafile)
            return
        reader = csv.reader(open(datafile, 'rb'))
        self.keys = reader.next()[1:]
        for row in reader:
            attribs = {}
            for k, a in zip(self.keys, row[1:]):
                attribs[k] = a
            self.data[row[0]] = attribs

    def save(self, datafile=None):
        if not datafile: datafile = self.datafile
        writer = csv.writer(open(self.datafile, 'wb'))
        writer.writerow(['key'] + self.keys)
        for key, attribs in self.data.iteritems():
            writer.writerow([key]+[attribs[k] for k in self.keys])

    def getByAttrib(self, name, value):
        result = []
        for key, attribs in self.data.iteritems():
            if attribs[name] == value:
                result.append(key)

    def addAttrib(self, attrib):
        if attrib in self.keys:
            print '[data] attribute {0} is already present.'.format(attrib)
            return
        self.keys.append(attrib)
        for item in self.data.values():
            item[attrib] = None

    def removeAttrib(self, attrib):
        self.keys.remove(attrib)
        for item in self.data.values():
            del item[attrib]

    def add(self, key, attribs):
        a = {}
        for k in self.keys:
            if k in attribs:
                a[k] = attribs[k]
                del attribs[k]
            else:
                a[k] = None
        if len(attribs) is not 0:
            print '[data] Warning, the following attributes were skipped: {0}'.format(\
                ', '.join(['{0}:{1}'.format(a, b) for a, b in attribs.iteritems()]))
        self.data[key] = a

    def remove(self, key):
        del self.data[key]
