#!/usr/bin/python

import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

sys.path.append("/usr/local/openvswitch/pylib/vca")

class Mirror(object):
	def __init__(self, ovs_path, br, logfd, mirror_type, mirror_id):
		self.ovs_path = ovs_path
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.br = br
		self.logfd = logfd
		self.mirror_type = mirror_type
		self.mirror_id = mirror_id

	def dump(self, to_stdout):
		cmd = [ self.appctl_path, "bridge/dump-mirrors", self.br ]
		if (to_stdout == True):
			shell.execute_hdr("Mirror configuration", cmd)
		else:
			shell.execute_log(self.logfd, cmd)

	def show(self, to_stdout):
		cmd = [ self.appctl_path, "bridge/show-mirror", self.br,
			self.mirror_id ]
		if (to_stdout == True):
			shell.execute_hdr("Mirror info for " + self.mirror_id,
					  cmd)
		else:
			shell.execute_log(self.logfd, cmd)

	def __parse_show_mirror(self, match_pattern, field):
		cmd = [ self.appctl_path, "bridge/show-mirror", self.br,
			self.mirror_id ]
		mirror_show = shell.execute(cmd).splitlines()
		out = None
		process_this_block = False
		for line in mirror_show:
			line_tok = line.split()
			if (line_tok == None) or (line_tok == []):
				continue
			if (line_tok[0] == self.mirror_id):
				mirror_type = line_tok[2]
				if (mirror_type == self.mirror_type):
					process_this_block = True
				else :
					process_this_block = False
			if (process_this_block == True):
				if (line.find(match_pattern) < 0):
					continue
				out = line_tok[field]
				break
		return out

	def get_dst_ip(self):
		return self.__parse_show_mirror(self.mirror_id, 6)

	def get_nrefs(self):
		return self.__parse_show_mirror(self.mirror_id, 5)

	def get_internal_name(self):
		return self.__parse_show_mirror("Mirror Internal Name:", 3)
