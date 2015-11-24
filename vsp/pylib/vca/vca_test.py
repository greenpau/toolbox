#!/usr/bin/python


import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

class SUITE(object):
	def __init__(self, suite_name):
		self.suite_name = suite_name
		self.tests = []

	def register_test(self, TEST):
		self.tests.append(TEST)

	def print_summary(self):
		n_passed = 0
		n_failed = 0
		for test in self.tests:
			if (test.passed == True):
				n_passed = n_passed + 1
			else:
				n_failed = n_failed + 1
		print "Num tests: " + str(n_passed + n_failed) + " (Passed: " + str(n_passed) + ", Failed: " + str(n_failed) + ")"

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
