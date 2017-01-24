from utils import *
import curses
import sys
import re

# colour mode flags
M_NORMAL     = 1
M_COLOUR_PN  = 2
M_COLOUR_SCL = 4
M_COLOUR_ANY = M_COLOUR_PN | M_COLOUR_SCL


class CSVFormatter(object):

	def __init__(self, sep, grep=None):
		self.sep     = sep
		self.lines   = []
		self.headers = []
		self.widths  = []
		self.align   = []
		self.isnum   = []
		self.cmins   = []
		self.cmaxs   = []
		self.dirty   = []
		self.colsep  = '  '
		self.grep    = re.compile(grep) if grep is not None else None

	def _gen_hdr_str(self):
		tmpl = ''
		for i,c in enumerate(self.headers):
			tmpl += '{{:<{}s}}{}'.format(self.widths[i], self.colsep)
		return tmpl.format(*self.headers)

	def _gen_line_subtmpl(self,col):
		return '{{:{}{}s}}{}'.format(self.align[col], self.widths[col], self.colsep)

	def _gen_line_tmpl(self):
		tmpl = ''
		for i in range(len(self.headers)):
			tmpl += self._gen_line_subtmpl(i)
		return tmpl

	def read_header(self, line):
		self.headers = line.strip().split(self.sep)
		self.widths  = [ len(h) for h in self.headers ]
		self.align   = ['>']  * len(self.headers)
		self.isnum   = [True] * len(self.headers)
		self.cmins   = [+1E99] * len(self.headers)
		self.cmaxs   = [-1E99] * len(self.headers)
        
	def read_line(self, line):
		if self.grep and not self.grep.search(line):
			return

		data = line.strip().split(self.sep)

		if len(data) > len(self.headers):
			self.headers += [''] * (len(data) - len(self.headers))

		if len(data) > len(self.widths):
			extend = (len(data) - len(self.widths))
			self.widths += [0   ]  * extend
			self.align  += ['>' ]  * extend
			self.isnum  += [True]  * extend
			self.cmins  += [+1E99] * extend
			self.cmaxs  += [-1E99] * extend

		assert( len(self.widths) == len(self.headers) )
		assert( len(self.widths) == len(self.align) )
		assert( len(self.widths) == len(self.isnum) )
		assert( len(self.widths) == len(self.cmaxs) )
		assert( len(self.widths) == len(self.cmins) ) 

		for i in range(len(data)):
			self.widths[i] = max(len(data[i]), self.widths[i])
			self.align[i]  = '<' if not is_num(data[i]) else self.align[i]
			self.isnum[i]  = self.isnum[i] and is_num(data[i])
			if self.isnum[i]:
				f = float(data[i])
				self.cmins[i] = min(self.cmins[i],f)
				self.cmaxs[i] = max(self.cmaxs[i],f) 

		self.dirty.append(True)
		self.lines.append(data)

	def make_ready(self):
		self._row_tmpl = self._gen_line_tmpl()
		self._rowcol_tmpl = [ self._gen_line_subtmpl(c) for c in range(self.ncols()) ]

	def mark_dirty(self):
		self.dirty = [True] * self.nrows()

	def width(self):
		return sum(self.widths) + (len(self.widths)-1)*len(self.colsep)

	def ncols(self):
		return len(self.headers)

	def nrows(self):
		return len(self.lines)

	def get_header(self):
		return self._gen_hdr_str()

	def get_line(self, row):
		return self._row_tmpl.format(*self.lines[row])
		
	def get_element(self, row, col):
		return self.lines[row][col]
		
	def get_element_str(self, row, col):
		return self._rowcol_tmpl[col].format(self.get_element(row, col))
		
	def build_view(self, pad, rgx, mode, row_start=None, row_end=None, cmap=cmap4):
		self.make_ready() 
		if not row_start: row_start = 0
		if not row_end:   row_end   = self.nrows()
		for r in range(row_start, row_end):
			if not self.dirty[r]: continue
			self.dirty[r] = False
			for c in range(self.ncols()):
				x,y = self.log2phys(r,c)	
				attrs = 0
				if mode==M_COLOUR_PN and self.isnum[c]:
					f = float(self.get_element(r,c))
					if f > 0:
						attrs = attrs | curses.color_pair(11)
					elif f < 0:
						attrs = attrs | curses.color_pair(10)
					else:
						attrs = attrs | curses.color_pair(13)
				elif mode==M_COLOUR_SCL and self.isnum[c]:
					f = float(self.get_element(r,c))
					f = float(f - self.cmins[c]) / float(self.cmaxs[c]-self.cmins[c])
					attrs = attrs | curses.color_pair(tcol(*cmap(f)))
				
				el = self.get_element_str(r,c)
				addstr(pad, x, y, el, attrs )
			
				if rgx is not None:
					attrs = attrs | curses.A_STANDOUT
					for m in rgx.finditer(el):
						substr = el[m.start(0):m.end(0)]
						addstr(pad, x, y+m.start(0), substr, attrs)

	def _pcol2lcol(self, coff_in):
		coff = 0
		for i in range(self.ncols()):
			coff += len(self.colsep) + self.widths[i]
			if coff_in < coff:
				return i
		raise ValueError("Physical column offset out-of-bounds")

	def _lcol2pcol(self, cidx_in):
		return sum(self.widths[:cidx_in]) + cidx_in*len(self.colsep)

	def log2phys(self, lrow, lcol):
		return (lrow, self._lcol2pcol(lcol))
	
	def phys2log(self, prow, pcol):
		return (prow, self._pcol2lcol(pcol))

	def find_next(self, rgx, row, col):
		for i in range(row, self.nrows()):
			j0 = 0 if (i>row) else col+2
			for j in range(j0, self.ncols()):
				if rgx.search(self.lines[i][j]):
					return (i,j)
		raise ValueError("No match")