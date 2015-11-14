#!/usr/bin/python

import abc

class SDK_OVS(object):
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def get_vswitchd_cmdline(self):
		""" retrieve ovs-vswitchd command line """
		return

	@abc.abstractmethod
	def get_ofport_request_arg(self, port_num):
		""" retrieve OFPort request argument """
		return

	@abc.abstractmethod
	def get_bridge_type_arg(self):
		""" retrieve OFProto bridge type argument """
		return
