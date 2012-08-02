from jazzr.tools import cgui
from jazzr.rhythm.parsers import *
import curses
from datetime import datetime

BEGIN = 0
STARTED = 1
ENDED = 2

def run(stdscr):
  onsets = []
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
    if c == ord('q'):
      if mode == BEGIN or mode == ENDED:
        break
      else:
        diff = datetime.now() - start
        onsets.append(diff.total_seconds())
        mode = ENDED

curses.wrapper(run)
