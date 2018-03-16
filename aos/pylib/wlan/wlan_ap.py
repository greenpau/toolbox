#!/usr/bin/python

import pexpect
import getpass
import time

import sys
sys.path.append("/usr/local/aos/pylib/wlan")
import wlan_controller

class Device():
	name = ""
	group = ""
	type = ""
	ip = ""
	c = None
	def __init__(self, c, name, group, ip, type):
		self.name = name
		self.group = group
		self.ip = ip
		self.type = "AP" + type
		self.c = c

	def get_nusers(self):
		return self.c.get_nusers(self.name)

class APList():
	naps = 0
	c = None
	apList = []
	def __init__(self, c=None):
		self.c = c
		if (self.c == None):
			return
		self.naps = int(self.c.get_naps("active"))
		self.__discover()

	def __discover(self):
		if (self.c == None):
			return 0
		if (self.naps == 0):
			return 0
		aplines = self.c.get_aplines("active")
		for i in range(0, int(self.naps)):
			apline = aplines[i].split()
			ap = Device(self.c, apline[0], apline[1], apline[2], apline[3])
			self.apList.append(ap)
		return self.naps

	def get_naps(self):
		return self.naps

	def info(self, index):
		if (index < len(self.apList)):
			return self.apList[index]
		else:
			return []
