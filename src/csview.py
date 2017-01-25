#!/usr/bin/env python3

import os
import re
import sys
import time
import gzip
import curses
import argparse as ap

from csvformat import *
from utils import *

if __name__ != "__main__":
	sys.exit(0)

#### COMMAND LINE ARGS

psr = ap.ArgumentParser('csv')
psr.add_argument('-d','--delim', type=str, default=',' )
psr.add_argument('-g','--grep',  type=str )
psr.add_argument('file',         type=str )
args = psr.parse_args()


#### READ FILE

# load
opnf = gzip.open if args.file.endswith('.gz') else open
fin  = opnf( args.file, 'r' )
csv  = CSVFormatter( args.delim, args.grep )
csv.read_header( fin.readline() )
chunk_size = 100000
loaded = False

def read_chunk():
	global csv,fin,loaded,chunk_size
	for _ in range(chunk_size):
		l = fin.readline()
		if '' == l:
			loaded = True
			break
		csv.read_line(l)


#### HELP

help_str = """
  CSViewer 

   h - Toggle this help message.
   c - Toggle colour mode.
   m - Next colour map (enter to finish).
   f - Go to end of file.
   g - Go to beginning of file.
   v - Go to first column.
   b - Go to last column.
   / - Search for regex.
   n - Next search result (if any).
   q - Quit.

  (djbarker 2017)
"""

#### MAIN

S_NORMAL = 1
S_QUERY  = 2

def main(screen):
	global help_str

	curses.curs_set(0)

	# set up colours
	curses.use_default_colors()
	
	for i in range(curses.COLORS):
		curses.init_pair(i+1, i, -1)

	if os.environ['TERM'] in ['xterm-256color']:
		cmodes = cycler([M_NORMAL,M_COLOUR_PN,M_COLOUR_SCL])
	elif os.environ['TERM'] in ['xterm']:
		cmodes = cycler([M_NORMAL,M_COLOUR_PN])
	else:
		cmodes = cycler([M_NORMAL])


	# l = logical, p = physical
	lcol = 0
	lrow = 0
	pcol = 0
	prow = 0

	cswW_old    = 0
	csvC_old    = 0
	csvH_old    = 0
	screenH_old = 0
	screenW_old = 0

	header = None
	body   = None
	status = None
	lines  = None
	
	last_c = ''
	hmode  = False
	mmode  = False
	smode  = S_NORMAL
	cmode  = next(cmodes)
	lineno = False
	rgx    = None
	
	# help window
	help_str = help_str.split('\n')
	helpH = len(help_str)
	helpW = max([len(l)+2 for l in help_str])
	help = curses.newpad(helpH,helpW)
	for i,l in enumerate(help_str):
		help.addstr(i,0,l)
	help.border()
	
	# color window
	cmapI = 0
	cmaps = [ cmap4, cmap1, cmap3, cmap2 ]
	cmapW = 56
	cmapH = len(cmaps) + 2
	cmap = curses.newpad(cmapH,cmapW)
	def build_cmap_win():
		l = 1
		for i in range(len(cmaps)):
			k = i + 1
			c1 = '>' if i==cmapI else '     '
			c2 = '<' if i==cmapI else '     '
			cmap.addstr(k, 1,       c1)
			cmap.addstr(k, cmapW-l-1, c2)
			for j in range(l+1, cmapW-l-1):
				f = (j-float(l))/(cmapW-2*float(l))
				cmap.addstr(k,j,'=',curses.color_pair(tcol(*cmaps[i](f))))
		cmap.border()
	
	while True:

		# detect screen size change
		screenH, screenW = screen.getmaxyx()
		changed = (screenH != screenH_old) or (screenW != screenW_old)
		screenH_old = screenH
		screenW_old = screenW
		col_shift = 5
		row_shift = screenH - 2

		# load data
		if (csv.nrows()-lrow <= 2*screenH) and not loaded:
			read_chunk()
			csvC = csv.ncols()
			csvH = csv.nrows()
			csvW = csv.width()
		changed = changed or (csvW != csvW_old) or (csvC != csvC_old) or (smode==S_QUERY)
		csvC_old = csvC
		csvH_old = csvH
		csvW_old = csvW
		
		# build display
		if changed:
			lineW = len(str(csv.nrows()))+1
			lineW = max(lineW, len('line '))
			lines  = curses.newpad(screenH, lineW)
			body   = curses.newpad(screenH, max(csvW,screenW))
			header = curses.newpad(1,       max(csvW,screenW))
			status = curses.newwin(1,       max(csvW,screenW), screenH-1,0)
					
			hattrs = curses.A_STANDOUT
			lattrs = curses.A_STANDOUT
			#if cmode != M_NORMAL:
			#	hattrs = hattrs | curses.color_pair(12)
			#	lattrs = lattrs | curses.color_pair(12)
			
			for i in range(csv.nrows()):
				addstr(lines, i, 0, '{{:<{}d}}'.format(lineW).format(i), lattrs)	
			
			csv_header = csv.get_header()
			addstr(header,0,0, ''.join([' ']*screenW), hattrs)
			addstr(header,0,0, csv_header, hattrs)
			csv.mark_dirty()
			screen.refresh()
			
		brow_start = prow
		brow_end   = min(prow + screenH, csvH)
		csv.build_view(body, rgx, cmode, brow_start, brow_end, cmaps[cmapI])

		# display display
		if lineno:
			loffset = lineW
			line_hdr = '{{:<{}s}}'.format(lineW).format('line')
			addstr(screen,0,0,line_hdr, hattrs)
			lines.refresh(prow,0,1,0,screenH-2,lineW-1)
		else:
			loffset = 0
		header.refresh(0,pcol,0,loffset,0,screenW-1)
		body.refresh(0,pcol,1,loffset,screenH-2,screenW-1)

		if smode == S_NORMAL:
			status_pad = ''.join([' ']*screenW)
			status_ldd = '' if loaded else ' (loaded)'
			status_str = ' pos {},{} // {}{} rows x {} cols{}'.format(
			prow,pcol,csvH,status_ldd,csvC,status_pad )

		# display status
		status_str += ''.join([' ']*(screenW - len(status_str)))
		addstr(status,0,0, status_str, hattrs)
		status.refresh()
		smode = S_NORMAL

		# display colourmap chooser
		if mmode:
			build_cmap_win()
			cmap.refresh(0,0
				,screenH//2-cmapH//2,screenW//2-cmapW//2
				,screenH//2+cmapH//2,screenW//2+cmapW//2 )
		
		# display help
		if hmode:
			help.refresh(0,0
				,screenH//2-helpH//2,screenW//2-helpW//2
				,screenH//2+helpH//2,screenW//2+helpW//2 )		
		
		# input
		prow_end = max(csvH - screenH + 2,0)
		pcol_end = max(csvW - screenW + loffset, 0)
		c = screen.getch() if last_c != '' else '.'
		if charcmp(c, 'q'):
			break
		elif charcmp(c, 'h'):
			hmode = not hmode
		elif charcmp(c, 'm') and cmode==M_COLOUR_SCL:
			if mmode:
				cmapI = (cmapI+1) % len(cmaps)
				csv.mark_dirty()
			else:
				mmode = True
		elif charcmp(c, ['\n','\r',curses.KEY_ENTER]):
			if mmode:
				mmode = False
		elif charcmp(c, curses.KEY_LEFT):
			pcol   = max(pcol-col_shift, 0)
		elif charcmp(c, curses.KEY_RIGHT):
			pcol   = min(pcol+col_shift, pcol_end )
		elif charcmp(c, curses.KEY_DOWN):
			prow = min(prow+1, prow_end)
			csv.mark_dirty()
		elif charcmp(c, curses.KEY_UP):
			prow = max(prow-1, 0)
			csv.mark_dirty()
		elif charcmp(c, curses.KEY_PPAGE):
			prow = max(prow-row_shift, 0)
			csv.mark_dirty()
		elif charcmp(c, curses.KEY_NPAGE):
			prow = min(prow+row_shift, prow_end)
			csv.mark_dirty()
		elif charcmp(c, 'f'):
			prow = prow_end
		elif charcmp(c, 'g'):
			prow = 0
		elif charcmp(c, 'v'):
			pcol = 0
		elif charcmp(c, 'b'):
			pcol = pcol_end
		elif charcmp(c, 'l'):
			lineno = not lineno
			loffset = lineW if lineno else 0
		elif charcmp(c, 'n') and rgx:
			(lrow,lcol) = csv.find_next(rgx, lrow, lcol)
			(prow,pcol) = csv.log2phys(lrow, lcol)
		elif charcmp(c, '/'):
			# search
			rgx = get_user_input(status, "Query: ")
			if ''==rgx: rgx = None
			try:
				status_str = 'Query: {}'.format(rgx)
				rgx = re.compile(rgx)
				(lrow,lcol) = csv.find_next(rgx, lrow, lcol)
				(prow,pcol) = csv.log2phys(lrow, lcol)
			except re.error:
				status_str = 'Invalid regex: {}'.format(rgx)
				rgx = None
			except ValueError as e:
				status_str = 'No match!'.format(e)
			except:
				pass
			smode = S_QUERY
			csv.mark_dirty()
		elif charcmp(c, 'c'):
			csv.mark_dirty()
			cmode = next(cmodes)
			smode = S_QUERY
			mmode = False
			status_str = 'Colour mode: {}'.format({
				M_NORMAL: 'Off', M_COLOUR_PN: 'PlusMinus', M_COLOUR_SCL: 'Scale'
				}[cmode])
 
		prow_end = max(csvH - screenH + 2,0)
		pcol_end = max(csvW - screenW + loffset, 0)
		prow = clamp(prow, 0, prow_end)
		pcol = clamp(pcol, 0, pcol_end)
		last_c = c

	curses.curs_set(1)

if __name__=='__main__':
	curses.wrapper(main)
