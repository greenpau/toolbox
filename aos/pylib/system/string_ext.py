#!/usr/bin/python

import sys
sys.path.append("/usr/local/aos/pylib/system")

def sans_firstline(inbuf):
	if (inbuf == ""):
		return ""
	first_newline_idx = inbuf.index("\n")
	if (first_newline_idx == -1):
		return inbuf
	outbuf = inbuf[first_newline_idx + 1:]
	return outbuf

def sans_lastline(inbuf):
	if (inbuf == ""):
		return ""
	last_newline_idx = inbuf.rfind('\n')
	if (last_newline_idx == -1):
		return inbuf
	outbuf = inbuf[:last_newline_idx]
	return outbuf

def sans_first_and_last_line(inbuf):
	return sans_firstline(sans_lastline(inbuf))

