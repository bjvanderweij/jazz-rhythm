#!/usr/bin/python

import curses


def test(stdscr):
  #curses.curs_set(0)
  stdscr.addstr(6, 0, 'HAHAHAHAHAHA!\tTAB\nNEWLINE')
  curses.mousemask(curses.BUTTON1_CLICKED)
  y = x = 0
  stdscr.addstr(9, 10, 'Max X: {0}, Max Y: {1}'.format(stdscr.getmaxyx()[1], stdscr.getmaxyx()[0]))
  while True:
    stdscr.move(y, x)
    stdscr.refresh()
    c = stdscr.getch()
    if c == curses.KEY_MOUSE:
      (id, x, y, z, state) = curses.getmouse()
      if state == curses.BUTTON1_CLICKED:
        stdscr.addstr(y, x, 'BOEM')
    elif c == ord('q'): break  # Exit the while()
    elif c == curses.KEY_HOME: x = y = 0
    elif c == curses.KEY_LEFT: x -= 1
    elif c == curses.KEY_RIGHT: x += 1
    elif c == curses.KEY_UP: y -= 1
    elif c == curses.KEY_DOWN: y += 1
    elif chr(c) == 'b': stdscr.addstr(y, x, 'BOEM')

curses.wrapper(test)
