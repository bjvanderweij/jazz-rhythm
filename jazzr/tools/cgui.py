import curses, math

def calert(stdscr, message, block=True):
  my, mx = stdscr.getmaxyx()
  curses.curs_set(0)
  lines = message.split('\n')
  height = 4 + len(lines)
  width = max([len(line) for line in lines]) + 8
  win = curses.newwin(height, width, my/2-height/2, mx/2-width/2)
  win.border(0)
  for i in range(len(lines)):
    win.addstr(2 + i, 4, lines[i])
  win.refresh()
  if block:
    stdscr.getch()

def cmenu(stdscr, message, items, h=30, w=40, ypos=5, xpos=5, cancel=True):

  curses.curs_set(1)
  my, mx = stdscr.getmaxyx()

  win = curses.newwin(h, w, ypos, xpos)
  win.border(0)
  win.addstr(0, 1, message)
  win.addstr(h-1, 1, '[(s)elect] [(c)ancel]')

  ph = len(items)+1
  pw = max([len(i.expandtabs()) for i in items])
  pad = curses.newpad(ph, pw)
  for i in range(0, len(items)):
    pad.addstr(i, 0, repr(items[i]))

  r = -1
  c = 0
  # Pad position
  x = y = 0
  # Cursor position
  cx = cy = 0
  while c != ord('c') and c != ord('q'):
    stdscr.addstr(my-1, 0, 'y={0} x={1} cy={2}, cx={3}'.format(y, x, cy, cx))
    win.refresh()
    pad.refresh(y, x, ypos+1, xpos+1, ypos+h-2, xpos+w-2)
    stdscr.move(ypos+1+cy, xpos+1+cx)
    c = stdscr.getch()
    if c == curses.KEY_DOWN:
      if cy < h-3 and cy < len(items):
        cy += 1
      elif y < len(items) - (h-2) and cy < len(items) - 1:
        y += 1
    elif c == curses.KEY_UP:
      if cy > 0:
        cy -= 1
      elif y > 0:
        y -= 1
    elif c == curses.KEY_LEFT:
      if x > 0:
        x -= 1
    elif c == curses.KEY_RIGHT:
      if x < pw - (w-2):
        x += 1
    elif c == ord('s') or c == curses.KEY_ENTER or c == 10:
      r = cy + y
      break
  
  win.clear()
  pad.clear()
  return r

def trackview(stdscr, tracks, width=40, ypos=5, xpos=5, scale=10):
  height = len(tracks) + 1
  length = max([t.length() for t in tracks])
  length /= 1000000.0
  viewwidth = int(math.ceil(length * scale))

  view = curses.newpad(height, viewwidth+1)
  win = curses.newwin(height, 8, ypos, xpos)

  win.addstr(0, 0, 'time (s)')
  for i in range(len(tracks)):
    win.addstr(i+1, 0, '#{0}'.format(tracks[i].n))
#  status.addstr(height - 1, 0, 'Time:{0}\tTime left: {1}\tScale: {2}'.format(0, 0, scale))
  
  trackrolls = {}
  data = {}
  for i in range(len(tracks)):
    positions = {}
    for j in range(len(tracks[i])):
      on = tracks[i].midifile.ticks_to_microseconds(tracks[i][j].on)
      pos = int(math.floor((on / 1000000.0)*scale))
      positions[str(pos)] = 1

    data[str(tracks[i].n)] = positions
    roll = ['-'] * viewwidth
    for posstr in positions.keys():
      roll[int(posstr)] = 'o'

    rollstr = ''.join(roll)
    trackrolls[str(tracks[i].n)] = rollstr
    view.addstr(i+1, 0, rollstr)

  return(data, win, view)

def updatetracks(stdscr, viewpos, time, (data, win, view), width=40, ypos=5, xpos=5, scale=10, currenttrack=None):
  height = len(data) + 2
  win.refresh()
  view.refresh(0, int(round(viewpos)), ypos, xpos+8, ypos+height, xpos+width)
  if time*scale > viewpos and time*scale < viewpos+width-8:
    i = 1
    stdscr.addstr(ypos, int(xpos+8+math.floor(time*scale-viewpos)), '|')
    for track in data.keys():
      symb = '|'
      pos = math.floor(time*scale)
      if str(int(pos)) in data[track] and currenttrack and int(track) == currenttrack:
        symb = 'O'
      stdscr.addstr(ypos+i, int(xpos+8+math.floor(time*scale-viewpos)), symb)
      i += 1

def prompt(stdscr, message, length=15):
  my, mx = stdscr.getmaxyx()
  height = 6
  width = max(length, len(message))+4
  win = curses.newwin(height, width, my/2-height/2, mx/2-width/2)
  win.addstr(1, 2, message)
  win.border(0)
  win.refresh()
  curses.echo()
  inp = win.getstr(3, 2, length)
  curses.noecho()
  win.clear()
  return inp
