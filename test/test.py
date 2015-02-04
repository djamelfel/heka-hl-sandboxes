import unittest
import socket
import subprocess
import os
import time
import json
import tempfile
import shutil

TCP_IP = 'localhost'
TCP_PORT = 5005

def setUpModule():
	global PROC
	global TEMP_DIR

	TEMP_DIR = tempfile.mkdtemp()
	PROC = subprocess.Popen(['hekad', '-config', 'heka.toml'], stderr=subprocess.PIPE)
	time.sleep(1)

def tearDownModule():
	global PROC
	global TEMP_DIR

	PROC.terminate()
	shutil.rmtree(TEMP_DIR)

class TestAddFields(unittest.TestCase):
	def setUp(self):
		global TEMP_DIR
		with open(TEMP_DIR + '/add_fields.toml', 'w') as f:
			f.write("""
				[AddFieldsFilter]
				type = "SandboxFilter"
				message_matcher = "Type == 'add.fields'"
				[AddFieldsFilter.config]
				fields = "uuid"
				uuid = "uuid_test"
				type_output = "output"
			""")
			f.flush()
		subprocess.check_call(['heka-sbmgr', '-action=load', '-config=PlatformTest.toml', '-script=' + os.path.abspath('..') + '/filters/add_static_fields.lua', '-scriptconfig=' + TEMP_DIR + '/add_fields.toml'])
		self.cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.cs.connect((TCP_IP, TCP_PORT))

	def tearDown(self):
		self.cs.close()
		subprocess.check_call(['heka-sbmgr', '-action=unload', '-config=PlatformTest.toml', '-filtername=AddFieldsFilter'])
		os.remove("output.log")

	def test_sandbox(self):
		time.sleep(1)
		self.cs.send(json.dumps({'Timestamp': 10, 'Type': 'add.fields', 'Payload': 'titi', 'Fields': {'name': 'tata', 'value': 'toto'}})+'\n')
		time.sleep(1)
		fi = open('output.log', 'r')
		for line in fi:
			data = json.loads(line)
			self.assertEqual(data['Fields']['uuid'], 'uuid_test')

if __name__ == '__main__':
	unittest.main()
