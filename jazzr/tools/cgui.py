import curses, math

def alert(stdscr, message, block=True):
  my, mx = stdscr.getmaxyx()
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

def menu(stdscr, message, items, height=0, width=0, cancel=True):

  curses.curs_set(1)
  my, mx = stdscr.getmaxyx()

  padheight = len(items)+1
  padwidth = max([len(i.expandtabs()) for i in items] + [len(message), 21])


  lines = message.split('\n')
  if not height: 
    height = padheight+len(lines)+3
  if not width:
    width = padwidth + 2

  ypos = my/2 - height/2
  xpos = mx/2 - width/2
  win = curses.newwin(height, width, ypos, xpos)
  win.border(0)
  for i in range(len(lines)):
    win.addstr(1+i, 1, lines[i])
  win.addstr(height-1, 1, '[(s)elect] [(c)ancel]')

  pad = curses.newpad(padheight, padwidth)
  for i in range(0, len(items)):
    pad.addstr(i, 0, items[i])

  response = -1
  c = 0
  # Pad position
  x = y = 0
  # Cursor position
  cursor = 0
  while c != ord('c') and c != ord('q'):
    if cursor > padheight:
      padheight = -padheight+1-cursor
    stdscr.addstr(my-1, 0, 'y={0} x={1} cursor={2}'.format(y, x, cursor))
    win.refresh()
    pad.refresh(y, x, ypos+2+len(lines), xpos+1, ypos+2+len(lines)+padheight, xpos+1+padwidth)
    stdscr.move(ypos+2+len(lines)+cursor-y, xpos+1)
    c = stdscr.getch()
    if c == curses.KEY_DOWN:
      if cursor+1 < len(items):
        cursor += 1
    elif c == curses.KEY_UP:
      if cursor > 0:
        cursor -= 1
    elif c == ord('s') or c == curses.KEY_ENTER or c == 10:
      response = cursor
      break
  
  win.clear()
  pad.clear()
  return response

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
