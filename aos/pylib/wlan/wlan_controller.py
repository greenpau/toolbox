#!/usr/bin/python

import pexpect
import getpass

import sys
sys.path.append("/usr/local/aos/pylib/wlan")

class Device(object):
	hostname = None
	admin = "admin"
	admin_pass = "admins"
	ssh_newkey = 'Are you sure you want to continue connecting'
	p = None

	def __init__(self, hostname):
		self.hostname = hostname
		self.login()

	def login(self):
		p = pexpect.spawn('ssh ' + self.admin + '@' + self.hostname)
		i = p.expect([self.ssh_newkey, 'password:', pexpect.EOF,
			      pexpect.TIMEOUT], 1)
		p.sendline(self.admin_pass)
		p.expect('.*#')
		self.p = p

	def get_boot_partition(self):
		if self.p == None:
			self.login()
		self.p.sendline('show image version')
		self.p.expect('.*#')
		partition = ""
		for l in self.p.after.splitlines():
			if l.find("Default boot") == -1:
				continue
			partition = l.split(":")[2].split(" ")[0]
			break
		return partition

	def scp_file(self, src_host, src_user, src_path, dst_path):
		if self.p == None:
			self.login()
		cmd = "copy scp: " + src_host + " " + src_user + " " + src_path + " " + dst_path
		print cmd
		self.p.sendline(cmd)
		self.p.expect('.*Password:')
		password = getpass.getpass(src_user + '@' + src_host + ' password: ')
		self.p.sendline(password)
		self.p.expect('.*#', timeout=300)
		print self.p.after
