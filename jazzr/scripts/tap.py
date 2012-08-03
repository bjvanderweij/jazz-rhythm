from jazzr.tools import cgui
from jazzr.rhythm.parsers import *
import curses
from datetime import datetime

BEGIN = 0
STARTED = 1
ENDED = 2

def run(stdscr):
  onsets = []
  parses = None
  mode = BEGIN
  while True:
    stdscr.clear()
    if mode == BEGIN:
      stdscr.addstr(3, 3, 'Tap space to begin and add an onset, hit b to begin and not add an onset, hit q to stop')
    elif mode == STARTED:
      stdscr.addstr(3, 3, 'Running. Tap space to add onsets, q to stop')
    elif mode == ENDED:
      stdscr.addstr(3, 3, 'Done. Onsets: {0}'.format(onsets))
    stdscr.refresh()
    c = stdscr.getch()
    if c == ord('b'):
      if mode == BEGIN:
        mode = STARTED
        start = datetime.now()
    if c == ord(' '):
      if mode == BEGIN:
        mode = STARTED
        start = datetime.now()
        onsets.append(0)
      elif mode == STARTED:
        diff = datetime.now() - start
        onsets.append(diff.total_seconds())
    if c == ord('r'):
      mode = BEGIN
      onsets = []
      parses = None
    if c == ord('q'):
      if mode == BEGIN or mode == ENDED:
        break
      else:
        diff = datetime.now() - start
        onsets.append(diff.total_seconds())
        mode = ENDED
    if c == ord('p') and mode == ENDED:
      if parses == None:
        cgui.alert(stdscr, 'Parsing', block=False)
        parser = StochasticParser(annotations.corpus('explicitswing'))
        parses = parser.parse_onsets(onsets)
      if len(parses) > 0:
        choice = cgui.menu(stdscr, '{0} parses'.format(len(parses)), ['View analysis', 'View score', 'View all'])
        if choice == -1: continue
        elif choice == 0:
          parse = parses[cgui.menu(stdscr, 'parse?', ['Prior: {0}, likelihood {1}, posterior {2}. Depth {3}'.format(p.prior, p.likelihood, p.posterior, p.depth) for p in parses])]
          parse.view()
        elif choice == 1:
          barlevel = cgui.prompt(stdscr, 'Barlevel?')
          parse = parses[cgui.menu(stdscrt, 'parse?', ['Prior: {0}, likelihood {1}, posterior {2}. Depth {3}'.format(p.prior, p.likelihood, p.posterior, p.depth) for p in parses])]
          parse.score(barlevel=int(barlevel))
        elif choice == 2:
          latex.view_symbols(parses, scale=False)
      else:
        cgui.alert(stdscr, 'No parses')
curses.wrapper(run)
