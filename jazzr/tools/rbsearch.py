from jazzr.tools import commandline, cgui
import sys, os, math, re, csv

books = ['RB1','RB2','RB3','NRB1', 'NRB2', 'NRB3', 'JLTD']
offsets = {'RB1':13,'RB2':7,'RB3':7,'NRB1':13, 'NRB2':12, 'NRB3':10, 'JLTD':7}

path = '/home/bastiaan/Courses/Jazz-Rhythm/Data/realbooks/index.csv'
songspath = '/home/bastiaan/Courses/Jazz-Rhythm/Data/realbooks/songs/'
bookspath = '/home/bastiaan/Courses/Jazz-Rhythm/Data/realbooks/index.csv'

def load_file(path=path):
  index = {}
  reader = csv.reader(open(path, 'rb'))
  # Skip header
  reader.next()

  for row in reader:
    items = {}
    i = 1
    for book in books:
      if row[i] is '':
        items[book] = None
      else:
        items[book] = int(row[i])
      i += 1
    index[row[0]] = items

  for book in books:
    ordered = sorted([(key, index[key][book]) for key in index.keys()], key=lambda x: x[1])
    for i in range(0, len(ordered)):
      (song, page) = ordered[i]
      if not page: continue
      nextpage = page
      if i < len(ordered) - 1:
        nextpage = ordered[i+1][1]
      index[song][book] = (page, page + (nextpage - page - 1))
  return index

def find(index, query):
  results = []
  for item in index.keys():
    if re.search(query, item.lower()):
      results.append(item)
    elif re.search(query, item.lower().replace('\'', '').replace('"', '')):
      results.append(item)
  return results

def save(index, bookspath, song, book, path, uninterrupted=False):
  (begin, end) = index[song][book]
  command = "pdftk A={0}{1}.pdf cat {2}-{3} output {4}".format(bookspath, book, str(begin), str(end), path)
  exitstatus = os.system(command)
  if exitstatus:
    print command
    if not uninterrupted:
      if raw_input('Process unsuccesful (exit status {0}), abort? (y/n) '.format(exitstatus)) is 'y':
        exit(0)

# This works if songs are stored as separate files in songpath
def view(song, book, songspath=songspath): 
  filename = '{0}-{1}.pdf'.format(song.replace(' ', '_').replace('\'', '\\\''), book)
  os.system('evince {0}{1} &'.format(songspath, filename))

def choose_book(index, results, stdscr=None):
  if stdscr:
    song = results[cgui.menu(stdscr, "Select a song", results)]
  else:
    song = results[commandline.menu("Select a song", results)]
  locations = zip(books, index[song])

  bookhits = []
  for book in books:
    if index[song][book]:
      bookhits.append(book)
  if stdscr:
    book = bookhits[cgui.menu(stdscr, "Select a book", bookhits)]
  else:
    book = bookhits[commandline.menu("Select a book", bookhits)]
  return (song, book)

def interactive(path=path, songspath=songspath):
  index = load_file(path)
  while True:
    query = raw_input('Say a name! ').lower()
    results = find(index, query)
    if len(results) > 0:
      (song, book) = choose_book(index, results)

      print "What would you like to do?"
      while True:
        choice = commandline.menu("Please select", ["View", "Continue", "Quit"])
        if choice is 0:
          view(song, book, songspath)
        if choice is 1: break
        if choice is 2: exit(0)

# Run once parsing function
# (Combines data from inf and datafile in newdatafile)
def parse_rawindex(inf, datafile, newdatafile):
  reader = csv.reader(open(inf, 'rb'))
  dreader = csv.reader(open(datafile, 'rb'))

  data = {}
  for row in dreader:
    data[row[0].lower()] = row[:]

  for row in reader:
    name = row[0].strip()
    page = int(row[1].strip())
    book = row[2].strip()

    if not name.lower() in data:
         
      pages = []
      for b in books:
        if b == book:
          pages.append(page + offsets[book])
        else: 
          pages.append(None)
      print [name] + pages
      data[name.lower()] = [name] + pages

  writer = csv.writer(open(newdatafile, 'wb'))
  writer.writerow(['Song'] + books)
  for key, value in sorted(data.iteritems(), key=lambda x: x[0]):
    writer.writerow(value)


# This was a run-once function  
def parse_file(inf, out):
  infile = open(inf)
  ofile = csv.writer(open(out, 'wb'))
  books = ['RB1','RB2','RB3','NRB1', 'NRB2', 'NRB3', 'JLTD']
  offsets = {'RB1':13,'RB2':7,'RB3':7,'NRB1':13, 'NRB2':12, 'NRB3':10, 'JLTD':7}
  infile.next()
  ofile.writerow(['Song'] + books)
  for line in infile:
    name = line[:43].strip()
    pages = {}
    values = []
    for i in range(len(books)):
      left = 43+i*7
      right = 43+i*7+7
      if right >= len(line): right = len(line) - 1
      page = line[left:right].strip()
      m = re.match('S([0-9]+)', page)
      if m:
        page = m.group(1)
      if not page is '':
        values.append(int(page) + offsets[books[i]])
      else:
        values.append(None)

    ofile.writerow([name] + values)

