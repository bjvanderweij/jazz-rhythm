import curses, curses.ascii, os, cgui


def test(stdscr):
  #curses.curs_set(0)
  my, mx = stdscr.getmaxyx()
  y = x = 0

#  stdscr.addstr(6, 0, 'HAHAHAHAHAHA!\tTAB\nNEWLINE')
  curses.mousemask(curses.BUTTON1_CLICKED)

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
    elif c == curses.KEY_LEFT: 
      if x > 0: x -= 1
    elif c == curses.KEY_RIGHT: 
      if x < mx-1: x += 1
    elif c == curses.KEY_UP: 
      if y > 0: y -= 1
    elif c == curses.KEY_DOWN: 
      if y < my-1: y += 1
    elif c == ord('b'): stdscr.addstr(y, x, 'BOEM')
    elif c == ord('m'):
      filelist = sorted(os.listdir('/home/bastiaan/'))
      r = cgui.cmenu(stdscr, 'Choose a file!', filelist)
      stdscr.clear()
      if r >= 0:
        stdscr.addstr(0, 0, filelist[r])
      else:
        stdscr.addstr(0, 0, 'Cancelled')

curses.wrapper(test)
