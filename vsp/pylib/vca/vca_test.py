#!/usr/bin/python


import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

class TEST(object):
	def __init__(self, test_id, test_desc, handler, param):
		self.test_id = str(test_id)
		self.test_desc = test_desc
		self.handler = handler
		self.param = param

	def run(self):
		print "Testcase ID #" + str(self.test_id) + ": " + self.test_desc
		self.passed = self.handler(self.param)
		if (self.passed) :
			print "######################### Testcase ID #" + self.test_id + ": PASSED ############################"
		else:
			print "######################### Testcase ID #" + self.test_id + ": FAILED ############################"
		print
