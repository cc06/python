#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-07 10:33:38

import os
import time
import unittest2 as unittest

from pyspider.libs import utils
from pyspider.libs import rabbitmq

@unittest.skipIf(os.environ.get('IGNORE_RABBITMQ'), 'no rabbitmq server for test.')
class TestRabbitMQ(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with utils.timeout(3):
            self.q1 = rabbitmq.Queue('test_queue', maxsize=5)
            self.q2 = rabbitmq.Queue('test_queue', maxsize=5)
            self.q3 = rabbitmq.Queue('test_queue_for_threading_test')
        self.q2.delete()
        self.q2.reconnect()
        self.q3.delete()
        self.q3.reconnect()

    @classmethod
    def tearDownClass(self):
        self.q2.delete()
        self.q3.delete()
        del self.q1
        del self.q2
        del self.q3

    def test_10_put(self):
        self.assertEqual(self.q1.qsize(), 0)
        self.assertEqual(self.q2.qsize(), 0)
        self.q1.put('TEST_DATA1', timeout=3)
        self.q1.put('TEST_DATA2_中文', timeout=3)
        time.sleep(0.01)
        self.assertEqual(self.q1.qsize(), 2)
        self.assertEqual(self.q2.qsize(), 2)

    def test_20_get(self):
        self.assertEqual(self.q1.get(timeout=0.01), 'TEST_DATA1')
        self.assertEqual(self.q2.get_nowait(), 'TEST_DATA2_中文')
        with self.assertRaises(self.q1.Empty):
            self.q2.get(timeout=0.01)
        with self.assertRaises(self.q1.Empty):
            self.q2.get_nowait()

    def test_30_full(self):
        self.assertEqual(self.q1.qsize(), 0)
        self.assertEqual(self.q2.qsize(), 0)
        for i in range(2):
            self.q1.put_nowait('TEST_DATA%d' % i)
        for i in range(3):
            self.q2.put('TEST_DATA%d' % i)
        with self.assertRaises(self.q1.Full):
            self.q1.put('TEST_DATA6', timeout=0.01)
        with self.assertRaises(self.q1.Full):
            self.q1.put_nowait('TEST_DATA6')

    def test_40_multiple_threading_error(self):
        def put(q):
            for i in range(100):
                q.put("DATA_%d" % i)
        def get(q):
            for i in range(100):
                q.get()

        thread = utils.run_in_thread(put, self.q3)
        get(self.q3)
