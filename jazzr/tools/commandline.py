def menu(question, options, cancel=False, executableOptions=False):
  while True:
    c = 1
    print question
    if cancel:
      print "\t0: Cancel"
    for option in options:
      if executableOptions:
        option = option[0]
      print "\t{0}: {1}".format(c,option)
      c += 1
    try:
      inp = raw_input("?: ")
    except EOFError:
      print 'User cancelled'
      return -1
    try:
      choice = int(inp)
    except:
      continue
    if choice < 0 or choice > len(options):
      continue
    if choice == 0 and not cancel:
      continue
    break
  if executableOptions:
    options[choice-1][1]()
  return choice - 1
