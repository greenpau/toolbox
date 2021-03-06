#!/usr/bin/python


import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

class SUITE(object):
	def __init__(self, suite_name):
		self.suite_name = suite_name
		self.tests = []
		self.test_subset = []
		self.exit_on_failure = False
		self.n_sub_tests = 0
	
	def set_exit_on_failure(self, exit_on_failure):
		self.exit_on_failure = exit_on_failure

	def register_test_subset(self, test_subset):
		if len(test_subset) == 0:
			return
		self.test_subset.append(test_subset)

	def register_test(self, TEST):
		if len(self.test_subset) == 0:
			self.tests.append(TEST)
			return True
		this_test = []
		this_test.append(TEST)
		for t in this_test:
			for subset in self.test_subset:
				test_func = t.handler.__name__
				subset_testname = str(subset).replace("'", "").replace("[", "").replace("]", "")
				if (test_func == subset_testname):
					self.tests.append(TEST)
					return True
		return False

	def run(self, test_handlers, test_args):
		for handler in test_handlers:
			handler(test_args)

	def print_header(self):
		print ""
		for i in range(1,79):
			sys.stdout.write("#")
		print ""
		print "Suite Name: " + self.suite_name
		for i in range(1,79):
			sys.stdout.write("#")
		print ""

	def print_summary(self):
		n_passed = 0
		n_failed = 0
		for test in self.tests:
			if (test.listing == True):
				return
			self.n_sub_tests = self.n_sub_tests + test.n_sub_tests
			if (test.passed == True):
				n_passed = n_passed + 1
			else:
				n_failed = n_failed + 1
		print "Suite Summary:"
		print "Suite name: " + self.suite_name
		print "Num tests: " + str(n_passed + n_failed) + " (Passed: " + str(n_passed) + ", Failed: " + str(n_failed) + ")"
		print "Num sub-tests: " + str(self.n_sub_tests)

	def assert_test_result(self, test):
		if (test.passed != True) and (self.exit_on_failure == True):
			self.print_summary()
			sys.exit()

class TEST(object):
	def __init__(self, test_id, test_desc, handler, param):
		self.test_id = str(test_id)
		self.test_desc = test_desc
		self.handler = handler
		self.param = param
		self.passed = True
		self.n_sub_tests = 0
		self.listing = False

	def list(self):
		self.listing = True
		print self.test_desc + ":: " + self.handler.__name__

	def run(self):
		print "Testcase ID #" + str(self.test_id) + ": " + self.test_desc
		self.passed, self.n_sub_tests = self.handler(self.param)
		if (self.passed) :
			print "################## Testcase ID #" + self.test_id + ": PASSED (sub-tests: " + str(self.n_sub_tests) + ") ####################"
		else:
			print "################## Testcase ID #" + self.test_id + ": FAILED (sub-tests: " + str(self.n_sub_tests) + ") ####################"
		print
