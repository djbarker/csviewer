import curses
import time

def clamp(x,y,z):
	return min(max(x,y),z)

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
	r = clamp(2*(0.5-frac), 0, 1)
	g = clamp(2*(frac-0.5), 0, 1)
	b = (1-(2*(frac-0.5))**2)
	return tuple([int(5*x) for x in (r,g,b)])

def cmap2(frac):
	r = clamp(5*(0.75-frac), 0, 1)
	g = clamp(5*(frac-0.25), 0, 1)
	b = 0
	return tuple([int(5*x) for x in (r,g,b)])

def cmap3(frac):
	r = clamp(5*(0.75-frac), 0, 1)
	g = clamp(5*(frac-0.25), 0, 1)
	b = bump(frac, 0.25, 0.4, 0.6, 0.75)
	return tuple([int(5*x) for x in (r,g,b)])

def cmap4(frac):
	b = bump(frac, -0.1,  0.1,  0.4, 0.6)
	g = bump(frac,  0.1,  0.4,  0.6, 0.9)
	r = bump(frac,  0.4,  0.6,  0.9, 1.1)
	return tuple([int(5*x) for x in (r,g,b)])

def main(scr):

	curses.use_default_colors()

	intvl = .005	
	H,W = scr.getmaxyx()
	h,w = (0,0)
	for i in range(curses.COLORS):
		curses.init_pair(i+1, i, -1)
		
	for i in range(8):
		j = i+1
		scr.addstr(0,i,'#',curses.color_pair(j))
		scr.addstr(1,i,'#',curses.color_pair(j+8))
		scr.refresh()
		time.sleep(intvl)

	def tcol(r,g,b):
		return 17+int( b + 6*(g + 6*r) )

	i = 17;
	for r in range(6):
		for g in range(6):
			for b in range(6):
				s = '#' 
				scr.addstr(3 + g, b + 7*r, s, curses.color_pair(i))
				i += 1
				#scr.addstr(12,0,'{} vs {}'.format(i, tcol(r,g,b)))
				scr.refresh()
				time.sleep(intvl) 
			
	for i in range(233,256):
		scr.addstr(10,i-233, '#', curses.color_pair(i))
			
	def do_cmap(r,cmap):
		N = 100
		for i in range(N):
			f = i / float(N)
			scr.addstr(r,i, '#', curses.color_pair(tcol(*cmap(f))))
			scr.refresh()
			time.sleep(intvl) 
				
	do_cmap(12,cmap1)
	do_cmap(13,cmap2)
	do_cmap(14,cmap3)
	do_cmap(15,cmap4)
	
		
	
	scr.refresh()
	time.sleep(100)

curses.wrapper(main)
