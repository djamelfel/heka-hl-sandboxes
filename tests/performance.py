import unittest
import socket
import subprocess
import os
import sys
import time
import tempfile
import shutil
from random import randrange

NB_TRACKER_MAX = 1
TIMEOUT = 10
HEKA_TESTS_DIR = os.path.realpath(os.path.dirname(__file__))
HEKA_HL_DIR = os.path.realpath(os.path.join(HEKA_TESTS_DIR, '..'))
SYMLINK = ['filters', 'encoders', 'decoders']
ENV = {
    'HEKA_TESTS_DIR': HEKA_TESTS_DIR,
    'TRSERVER_INPUT_PORT': '6050',
}

def setUpModule():
    global OUTPUT
    global PROC
    global TMPCONFIG

    ENV['HEKA_HL_DIR'] = tempfile.mkdtemp(prefix='heka-hl-')
    OUTPUT = os.path.join(ENV['HEKA_HL_DIR'], 'output.txt')
    for link in SYMLINK:
        os.symlink(HEKA_HL_DIR + '/' + link, ENV['HEKA_HL_DIR'] + '/lua_' + link)

    TMPCONFIG = os.path.join(HEKA_HL_DIR + '/toml', 'tmp.toml')
    with open(TMPCONFIG, 'w') as f:
        f.write("""
[FileOutput]
message_matcher = "Type == 'heka.sandbox.trwebclient'"
path = '%ENV[HEKA_HL_DIR]/output.txt'
encoder = "CarbonEncoder"

[TestTserverInput]
type = "UdpInput"
address = ":%ENV[TRSERVER_INPUT_PORT]"
splitter = "TokenSplitter"
decoder = "TrserverDecoder"
        """)
        f.flush()

    if '-b' in sys.argv or '--buffer' in sys.argv:
        PROC = subprocess.Popen(
            ['/usr/bin/hekad', '-config', HEKA_HL_DIR + '/toml'],
            stdout=subprocess.PIPE,
            env=ENV)
    else:
        PROC = subprocess.Popen(['/usr/bin/hekad', '-config', HEKA_HL_DIR + '/toml'], env=ENV)
    time.sleep(1)

def tearDownModule():
    global PROC
    global OUTPUT

    PROC.terminate()
    os.remove(TMPCONFIG)
    shutil.rmtree(ENV['HEKA_HL_DIR'])


class HekaTestCase(unittest.TestCase):
    def send_metric(self, msg):
        self.heka_output.sendto(
            msg, ('localhost', int(ENV['TRSERVER_INPUT_PORT'])))

    @classmethod
    def setUpClass(self):
        self.heka_output = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @classmethod
    def tearDownClass(self):
        self.heka_output.close()


class TestPerformance(HekaTestCase):
    def test_flow_message(self):
        global OUTPUT

        sun_metrics = ['trserver_sun_roll', 'trserver_sun_tilt']
        metrics = ['accelerometer', 'Isensor1', 'Isensor2', 'sun_roll_angle',
                'sun_tilt_angle', 'wind', 'drive0_current', 'drive0_voltage',
                'drive1_current', 'drive1_sinceReset', 'drive2_current', 'roll2_encoder',
                'roll_angle', 'roll_encoder', 'roll_offset', 'tilt1_offset', 'tilt2_offset',
                'tilt_angle', 'tilt_encoder', 'drive0_sinceReset']
        time_sys = time.time()

        while(time.time() < time_sys + TIMEOUT):
            for metric in sun_metrics:
                self.send_metric('trserver_%s:%d|p\n' % (metric, randrange(90)))
            for num_tracker in range(1, NB_TRACKER_MAX+1):
                for metric in metrics:
                    self.send_metric('trserver_tracker%02d_%s:%d|p\n' % (num_tracker, metric, randrange(90)))
                self.send_metric('trserver_tracker%02d_mode:%d|p\n' % (num_tracker, randrange(7)))
            time.sleep(1)

        self.assertTrue(os.path.isfile(OUTPUT), "Error:  file: %s does\n't exist" % OUTPUT)
        self.assertNotEqual(os.stat(OUTPUT).st_size, 0, "Error:  file: %s is empty" % OUTPUT)

        last_metric = None
        with open(OUTPUT) as lines:
            for i, line in enumerate(lines, start=1):
                last_metric = line
                nbr_lines = i

        self.assertLess((int(last_metric.split()[2]) - time.time()), 2000, 'time pass out')
        nbr_lines_expected = (NB_TRACKER_MAX*(len(metrics)+1)+len(sun_metrics))*TIMEOUT
        self.assertEqual(nbr_lines, nbr_lines_expected, 'some data was lost')

if __name__ == '__main__':
    unittest.main()
