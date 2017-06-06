#!/usr/bin/python

import sys
import json

sys.path.append("/usr/local/openvswitch/pylib/system")

class Json_Config(object):
	def __init__(self, cfg_file, vlog):
		self.cfg_file = cfg_file
		self.vlog = vlog
		with open(cfg_file) as data_file:
			self.data = json.load(data_file)

	def __get_key_values(self, properties, keys):
		kv_pairs = [ ]
		for k in keys:
			kv_pair = { }
			kv_pair[k] = str(properties[k]).replace("u'", "")
			kv_pairs.append(kv_pair)
		return kv_pairs

	def read(self, attribute, keys):
		config = self.data[attribute]
		all_entries = [ ]
		for c in config:
			attrs = self.__get_key_values(c, keys)
			all_entries.append(attrs)
		return all_entries

	def count(self, attribute):
		config = self.data[attribute]
		return len(config)

	def exists(self, attribute, keys, value):
		config = self.data[attribute]
		for c in config:
			attrs = self.__get_key_values(c, keys)
			for a in attrs:
				for (k, v) in a.items():
					if (v == value):
						return True
		return False

	def search(self, attribute, keys, inpkey, inpvalue, inskey):
		config = self.data[attribute]
		found_pkey = False
		for c in config:
			attrs = self.__get_key_values(c, keys)
			for a in attrs:
				for (k, v) in a.items():
					if (k == inpkey) and (v == inpvalue):
						found_pkey = True
						break
			if (found_pkey == True):
				attrs = self.__get_key_values(c, keys)
				for a in attrs:
					for (k, v) in a.items():
						if (k == inskey):
							return v
		return None
