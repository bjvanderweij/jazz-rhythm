from numpy import *

def distance_matrix(s, t):
    m = len(s)
    n = len(t)

    D = zeros((m+1,n+1))

    for i in range(m+1):
        D[i,0] = i
    for j in range(n+1):
        D[0,j] = j

    for j in range(1,n+1):
        for i in range(1,m+1):
            if s[i-1] == t[j-1]:
                D[i,j] = D[i-1,j-1]
            else:
                D[i,j] = min([\
                    D[i-1, j] + 1,\
                    D[i, j-1] + 1,\
                    D[i-1, j-1] + 1\
                    ])
    return D

def h(a, b):
    return 0
    #return (abs(a[0] - b[0]) + abs(a[1] - b[1])) / 2.0

def moves(D, node):
    m = [(node[0]+1, node[1]),\
        (node[0], node[1]+1),\
        (node[0]+1, node[1]+1)]
    n = []
    for move in m:
        if move[0] >= len(D) or move[1] >= len(D[0]):
            continue
        elif (node[0]+1,node[1]+1) != move and D[node[0], node[1]] == D[move[0],move[1]]:
            continue
        else:
            n.append(move)
    return n

def distance(D, x,y):
    if D[x[0], x[1]] == D[y[0], y[1]]:
        return 0
    else:
        return 1 #D[x[0],x[1]]

def reconstruct_path(came_from, current_node):
    if came_from[current_node] in came_from:
        p = reconstruct_path(came_from, came_from[current_node])
        return p + [current_node]
    else:
        return [current_node]

def find_match(D, s, t):
    # A star!
    start = (0,0)
    goal = (len(D)-1, len(D[0])-1)
    closedset = []
    openset = [start]
    came_from = {}
    g_score = {start:0}
    h_score = {start:h(start,goal)}
    f_score = {start:h_score[start]}

    while not len(openset) == 0:
        x = openset[0]
        lowest = f_score[x]
        for o in openset:
            if f_score[o] < f_score[x]:
                lowest = f_score[o]
                x = o
        if x == goal:
            return reconstruct_path(came_from, came_from[goal])

        openset.remove(x)
        closedset.append(x)
        for y in moves(D, x):
            if y in closedset:
                continue
            tentative_g_score = g_score[x] + distance(D,x,y)
            if not y in openset:
                openset.append(y)
                tentative_is_better = True
            elif tentative_g_score < g_score[y]:
                tentative_is_better = True
            else:
                tentative_is_better = False

            if tentative_is_better:
                came_from[y] = x
                g_score[y] = tentative_g_score
                h_score[y] = h(y, goal)
                f_score[y] = g_score[y] + h_score[y]

    print "Failure"


def print_nice(D, s, t):
    s = [" "] + [str(x) for x in s]
    t = [" "] + [str(x) for x in t]
    print '   ',
    for column in range(len(D[0])):
        print "{0}  ".format(t[column]),
    print "\n\n",
    for row in range(len(D)):
        print "{0}  ".format(s[row]),
        for column in range(len(D[row])):
            if(D[row,column] <= 0):
                print "\b({0}) ".format(int(-D[row, column])),
            else:
                print "{0}  ".format(int(D[row, column])),
        print "\n\n",


def match(a, b):
    D = distance_matrix(a, b)
    p = find_match(D,a,b)
    p = p + [(len(D)-1,len(D[0])-1)]
    m = {}
    for n in p:
        m[n[0]-1] = n[1]-1
    return m


if __name__ == '__main__':
    import sys
    s = sys.argv[1]
    t = sys.argv[2]
    D = distance_matrix(sys.argv[1], sys.argv[2])
    print_nice(D, s, t)
    print "Finding path"
    p = find_match(D, sys.argv[1], sys.argv[2])
    D[len(D)-1,len(D[0])-1] = -D[len(D)-1,len(D[0])-1]
    for n in p:
        D[n[0], n[1]] = -D[n[0],n[1]]
    print_nice(D, s, t)
