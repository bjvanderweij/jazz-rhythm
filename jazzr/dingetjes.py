def draw_chart(chart):
  coordinates = chart.keys()
  max_x = max(coordinates, key=lambda x: x[0])[0]
  max_y = max(coordinates, key=lambda x: x[1])[1]
  print '    ',
  for x in range(0, max_x+1):
    print '{0:4}'.format(x),
  print
  print
  for y in range(0, max_y+1):
    print '{0:4} '.format(y),
    for x in range(0, max_x+1):
      if (x, y) in chart:
        print '{0:4}'.format(chart[x,y]),
      else:
        print '    ',
    print 
    print

def chart1(n):
  counter = 0
  chart = {}
  for i in range(1, n+1):
    chart[i, i-1] = counter
    counter += 1
    for j in range(i-2, -1, -1):
      cell = []
      chart[i,j] = counter
      counter += 1
  return chart
        
def chart2(n):
  chart = {}
  counter = 0
  # Iterate over rows
  for j in range(1, n+1):
    # Fill diagonal cells
    chart[j-1, j] = counter
    counter += 1
    # Iterate over columns
    for i in range(j-2, -1, -1):
      chart[i,j] = counter
      counter += 1
  return chart

draw_chart(chart1(5))
