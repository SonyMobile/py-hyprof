#!/usr/bin/env python3
#coding=utf8

from datetime import datetime, timedelta
from unittest import TestCase

import hprof

class TestArtificialHprof(TestCase):
	def setUp(self):
		self.data = [
			bytearray(b'JAVA PROFILE 1.0.3\0'),
			bytearray(b'\0\0\0\4'), # id size
			bytearray(b'\x00\x00\x01\x68\xE1\x43\xF2\x63'), # timestamp
			bytearray(b'\xff\0\0\0\0\0\0\0\20\0\1\2\3Hello world!'),
			bytearray(b'\xff\0\1\0\0\0\0\0\x3d\3\2\1\1\x50\xe5\xad\xa6\x51ZYXWVUTSRQPONMLKJIHGFEDCBAabcdefghijklmnopqrstuvwxyz'),
			bytearray(b'\xff\2\0\0\0\0\0\0\10\3\4\5\6ABBA'),
			bytearray(b'\xff\0\0\0\0\0\0\0\0'),
		]
		self.f = None

	def tearDown(self):
		self.close()

	def open(self):
		self.close()
		self.f = hprof.open(b''.join(self.data))

	def close(self):
		if self.f is not None:
			self.f.close()
			self.f = None

	def test_correct_header(self):
		self.open()
		self.assertEqual(self.f.idsize, 4)
		self.assertEqual(self.f.starttime, datetime.fromtimestamp(0x168E143F263/1000))

	def test_correct_modified_header(self):
		self.data[1][3] = 8
		self.data[2][2] = 0
		self.data[2][7] = 0x64
		self.open()
		self.assertEqual(self.f.idsize, 8)
		self.assertEqual(self.f.starttime, datetime.fromtimestamp(0x68E143F264/1000))

	def test_incorrect_header(self):
		self.data[0][7] = ord('Y')
		with self.assertRaisesRegex(hprof.FileFormatError, 'bad header'):
			self.open()

	def test_incorrect_version(self):
		self.data[0][13] = ord('9')
		with self.assertRaisesRegex(hprof.FileFormatError, 'bad version'):
			self.open()

	def test_list_0_records(self):
		self.data = self.data[:3]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 0)

	def test_list_1_record(self):
		self.data = self.data[:4]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 1)

	def test_list_2_records(self):
		self.data = self.data[:5]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 2)

	def test_list_3_records(self):
		self.data = self.data[:6]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 3)

	def test_iteration(self):
		self.data = self.data[:6]
		self.open()
		recs = self.f.records()
		next(recs)
		next(recs)
		next(recs)
		with self.assertRaises(StopIteration):
			next(recs)

	def test_record_length(self):
		self.open()
		records = self.f.records()
		self.assertEqual(len(next(records)), 25)
		self.assertEqual(len(next(records)), 70)
		self.assertEqual(len(next(records)), 17)
		self.assertEqual(len(next(records)), 9)

	def test_record_tags(self):
		self.open()
		for i, r in enumerate(self.f.records()):
			self.assertEqual(r.tag, self.data[3+i][0])

	def test_record_time(self):
		self.open()
		base = 0x168e143f263 * 1000
		records = self.f.records()
		self.assertEqual(next(records).timestamp, datetime.fromtimestamp((base+0)/1000000))
		self.assertEqual(next(records).timestamp, datetime.fromtimestamp((base+0x10000)/1000000))
		self.assertEqual(next(records).timestamp, datetime.fromtimestamp((base+0x2000000)/1000000))
		self.assertEqual(next(records).timestamp, datetime.fromtimestamp((base+0)/1000000))

	def test_record_rawbody(self):
		self.open()
		recs = self.f.records()
		self.assertEqual(next(recs).rawbody, self.data[3][9:])
		self.assertEqual(next(recs).rawbody, self.data[4][9:])
		self.assertEqual(next(recs).rawbody, self.data[5][9:])
		self.assertEqual(next(recs).rawbody, self.data[6][9:])

	def test_record_str(self):
		self.open()
		for i, r in enumerate(self.f.records()):
			s = str(r)
			self.assertTrue(s.startswith('Unhandled('))
			self.assertTrue(s.endswith(')'))
			self.assertIn(''.join('%02x' % b for b in self.data[3+i][ 9:13]), s)
			self.assertIn(''.join('%02x' % b for b in self.data[3+i][13:17]), s)
			self.assertIn(''.join('%02x' % b for b in self.data[3+i][17:21]), s)
			self.assertIn(''.join('%02x' % b for b in self.data[3+i][21:25]), s)

	def test_unhandled_record(self):
		self.open()
		records = self.f.records()
		next(records)
		r = next(records)
		self.assertIs(type(r), hprof.record.Unhandled)
		self.assertEqual(r.tag, 255)
		self.assertEqual(r.timestamp, datetime.fromtimestamp(0x168e143f263 / 1000 + 0x10000 / 1000000))
		self.assertEqual(r.relative_timestamp, timedelta(microseconds = 0x10000))
		with self.assertRaisesRegex(AttributeError, 'has no id'):
			r.id
		self.assertEqual(len(r), 70)
		s = str(r)
		self.assertTrue(s.startswith('Unhandled('))
		self.assertTrue(s.endswith(')'))
		self.assertIn('03020101 50e5ada6', s)
