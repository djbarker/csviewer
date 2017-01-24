
import curses
from curses.textpad import Textbox, rectangle

#### GENERIC UTILS

def is_num(x):
    try:
        float(x)
    except ValueError:
        return False
    return True
	
def charcmp(c1,c2):
	if type(c2)==int:
		return c1==c2
	else:
		return (c1==ord(c2)) or (str(c1).lower()==c2) 
	
def clamp(x,mn,mx):
	return min(max(x,mn),mx)
	
def cycler(l):
	i = 0
	n = len(l)
	while True:
		yield l[i]
		i = (i+1)%n
		
		
#### TERM COLOUR UTILS

def bump(x,x01,x11,x12,x02):
	if x < x01:
		return 0.
	elif x < x11:
		return (x-x01)/(x11-x01)
	elif x < x12:
		return 1.
	elif x < x02:
		return 1. - (x-x12)/(x02-x12)
	else:
		return 0.

def cmap1(frac):
	"r->b->g"
	r = clamp(2*(0.5-frac), 0, 1)
	g = clamp(2*(frac-0.5), 0, 1)
	b = (1-(2*(frac-0.5))**2)
	return tuple([int(5*x) for x in (r,g,b)])

def cmap2(frac):
	"r->y->g"
	r = clamp(5*(0.75-frac), 0, 1)
	g = clamp(5*(frac-0.25), 0, 1)
	b = 0
	return tuple([int(5*x) for x in (r,g,b)])

def cmap3(frac):
	"r->w->g"
	r = clamp(5*(0.75-frac), 0, 1)
	g = clamp(5*(frac-0.25), 0, 1)
	b = bump(frac, 0.25, 0.4, 0.6, 0.75)
	b = clamp(b,0,1)
	return tuple([int(5*x) for x in (r,g,b)])


def cmap4(frac):
	"jet"
	b = bump(frac, -0.1,  0.1,  0.4, 0.6)
	g = bump(frac,  0.1,  0.4,  0.6, 0.9)
	r = bump(frac,  0.4,  0.6,  0.9, 1.1)
	return tuple([int(5*x) for x in (r,g,b)])
		
def tcol(r,g,b):
	return 17+int( b + 6*(g + 6*r) )
		
#### NCURSES UTILS
		
def addstr(screen, y, x, txt, *args, **kwargs):
    try:
        screen.addstr(y,x,txt,*args,**kwargs)
    except:
        pass

def get_par_coords(screen):
    parX,parY = screen.getparyx()
    if (parX==-1) and (parY==-1):
        return screen.getbegyx()
    else:
        return parX,parY

def get_user_input(screen, query):
    screenH, screenW = screen.getmaxyx()
    begH, begW = get_par_coords(screen)
    screen.clear()
    addstr(screen, 0, 0, query) 
    screen.refresh()
    in_area = curses.newwin(1, screenW, begH, begW + len(query))
    curses.curs_set(1)
    box = Textbox(in_area)
    box.edit()
    result = box.gather()
    curses.curs_set(0)
    return result.strip()
	