# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

from unittest import main, TestCase

import os.path

import hprof

inputfile = os.path.abspath(os.path.join(os.path.dirname(__file__), 'basic_reads.hprof'))


class TestCorners(TestCase):
	def test_modify_data(self):
		with hprof.HprofFile(inputfile) as bf:
			with self.assertRaisesRegex(TypeError, 'readonly'):
				bf._data[0] = 0x20

	def test_exit_cleanup(self):
		with hprof.HprofFile(inputfile) as bf:
			pass
		self.assertIsNone(bf._data)
		self.assertIsNone(bf._f)

	def test_read_from_bytes(self):
		f = hprof.HprofFile(b'JAVA PROFILE 1.0.3\0'
				+ b'\0\0\0\4'
				+ b'\0\0\0\1\2\3\4\5'
				+ b'\xff\0\0\0\0\0\0\0\10'
				+ b'ABCD\0EFG'
		)
		self.assertEqual(f.read_ascii(45,3), 'EFG')
		self.assertEqual(f.read_ascii(40), 'ABCD')
		self.assertEqual(f.read_uint(44), 0x00454647)
		with self.assertRaisesRegex(hprof.EofError, 'read.*48:49.*48'):
			f.read_byte(48)
		self.assertEqual(f.read_utf8(43,4), 'D\0EF')

	def test_invalid_ctor_arg(self):
		with self.assertRaises(TypeError):
			hprof.HprofFile(7)

	def test_missing_func_no_args(self):
		with hprof.HprofFile(inputfile) as bf:
			with self.assertRaisesRegex(AttributeError, 'missing_func'):
				bf.missing_func()

	def test_missing_func_str_arg(self):
		with hprof.HprofFile(inputfile) as bf:
			with self.assertRaisesRegex(AttributeError, 'missing_func'):
				bf.missing_func('3')

	def test_missing_func_int_arg(self):
		with hprof.HprofFile(inputfile) as bf:
			with self.assertRaisesRegex(AttributeError, 'missing_func'):
				bf.missing_func(3)

	def test_read_without_addr(self):
		with hprof.HprofFile(inputfile) as bf:
			with self.assertRaisesRegex(TypeError, 'addr'):
				bf.read_bytes()

	def test_read_without_nbytes(self):
		with hprof.HprofFile(inputfile) as bf:
			with self.assertRaisesRegex(TypeError, 'missing.*nbytes'):
				bf.read_bytes(0)

class TestByteReads(TestCase):
	def setUp(self):
		self.f = hprof.HprofFile(inputfile)

	def tearDown(self):
		self.f.close()

	def test_read_byte(self):
		self.assertEqual(self.f.read_byte(40), 0x41)
		self.assertEqual(self.f.read_byte(41), 0x42)
		self.assertEqual(self.f.read_byte(42), 0x43)
		self.assertEqual(self.f.read_byte(43), 0x44)
		self.assertEqual(self.f.read_byte(44), 0)
		self.assertEqual(self.f.read_byte(45), 0)
		self.assertEqual(self.f.read_byte(46), 0)
		self.assertEqual(self.f.read_byte(47), 0)
		self.assertEqual(self.f.read_byte(48), 0xc3)
		self.assertEqual(self.f.read_byte(49), 0xb6)
		self.assertEqual(self.f.read_byte(50), 0x46)
		self.assertEqual(self.f.read_byte(51), 0x00)
		self.assertEqual(self.f.read_byte(52), 0xaa)
		self.assertEqual(self.f.read_byte(53), 0x46)
		self.assertEqual(self.f.read_byte(54), 0x47)
		self.assertEqual(self.f.read_byte(55), 0x48)
		self.assertEqual(self.f.read_byte(56), 0x49)

	def test_read_byte_outside(self):
		with self.assertRaisesRegex(hprof.EofError, 'read.*57:58.*57'):
			self.f.read_byte(57)

	def test_read_byte_negative(self):
		with self.assertRaisesRegex(hprof.EofError, '-1'):
			self.f.read_byte(-1)

class TestByteArrayReads(TestCase):
	def setUp(self):
		self.f = hprof.HprofFile(inputfile)

	def tearDown(self):
		self.f.close()

	def test_read_bytes(self):
		self.assertEqual(self.f.read_bytes(40, 4), b'ABCD')
		self.assertEqual(self.f.read_bytes(44, 7), b'\0\0\0\0\xc3\xb6F')
		self.assertEqual(self.f.read_bytes(46, 4), b'\0\0\xc3\xb6')
		self.assertEqual(self.f.read_bytes(51, 3), b'\0\xaaF')

	def test_read_zero_bytes(self):
		self.assertEqual(self.f.read_bytes(42, 0), b'')
		self.assertEqual(self.f.read_bytes(41, 0), b'')
		self.assertEqual(self.f.read_bytes(40, 0), b'')
		self.assertEqual(self.f.read_bytes(56, 0), b'')

	def test_read_bytes_negative_count(self):
		with self.assertRaisesRegex(ValueError, '-1'):
			self.f.read_bytes(0, -1)
		with self.assertRaisesRegex(ValueError, '-3'):
			self.f.read_bytes(46, -3)

	def test_read_bytes_outside(self):
		with self.assertRaisesRegex(hprof.EofError, 'read.*57:58.*57'):
			self.f.read_bytes(57,1)

	def test_read_bytes_negative(self):
		with self.assertRaisesRegex(hprof.EofError, '-1'):
			self.f.read_bytes(-1,1)

	def test_read_bytes_spill(self):
		with self.assertRaisesRegex(hprof.EofError, 'read.*56:58.*57'):
			self.f.read_bytes(56,2)

	def test_read_bytes_edge(self):
		self.assertEqual(self.f.read_bytes(55,2), b'HI')
		self.assertEqual(self.f.read_bytes(56,1), b'I')
		self.assertEqual(self.f.read_bytes(57,0), b'')
		with self.assertRaisesRegex(hprof.EofError, '58.*57'):
			self.f.read_bytes(58,0)

class TestUintReads(TestCase):
	def setUp(self):
		self.f = hprof.HprofFile(inputfile)

	def tearDown(self):
		self.f.close()

	def test_read_uint(self):
		self.assertEqual(self.f.read_uint(40), 0x41424344)
		self.assertEqual(self.f.read_uint(41), 0x42434400)
		self.assertEqual(self.f.read_uint(42), 0x43440000)
		self.assertEqual(self.f.read_uint(43), 0x44000000)
		self.assertEqual(self.f.read_uint(44), 0)
		self.assertEqual(self.f.read_uint(45), 0x000000c3)
		self.assertEqual(self.f.read_uint(46), 0x0000c3b6)
		self.assertEqual(self.f.read_uint(47), 0x00c3b646)
		self.assertEqual(self.f.read_uint(48), 0xc3b64600)
		self.assertEqual(self.f.read_uint(49), 0xb64600aa)
		self.assertEqual(self.f.read_uint(50), 0x4600aa46)
		self.assertEqual(self.f.read_uint(51), 0x00aa4647)
		self.assertEqual(self.f.read_uint(52), 0xaa464748)
		self.assertEqual(self.f.read_uint(53), 0x46474849)

	def test_read_uint_spill(self):
		with self.assertRaisesRegex(hprof.EofError, 'read.*55:59.*57'):
			self.f.read_uint(55)

	def test_read_uint_outside(self):
		with self.assertRaisesRegex(hprof.EofError, '2000.*57'):
			self.f.read_uint(2000)

	def test_read_uint_negative(self):
		with self.assertRaisesRegex(hprof.EofError, '-2'):
			self.f.read_uint(-2)

class TestIntReads(TestCase):
	def setUp(self):
		self.f = hprof.HprofFile(inputfile)

	def tearDown(self):
		self.f.close()

	def test_read_uint(self):
		self.assertEqual(self.f.read_int(40), 0x41424344)
		self.assertEqual(self.f.read_int(41), 0x42434400)
		self.assertEqual(self.f.read_int(42), 0x43440000)
		self.assertEqual(self.f.read_int(43), 0x44000000)
		self.assertEqual(self.f.read_int(44), 0)
		self.assertEqual(self.f.read_int(45), 0x000000c3)
		self.assertEqual(self.f.read_int(46), 0x0000c3b6)
		self.assertEqual(self.f.read_int(47), 0x00c3b646)
		self.assertEqual(self.f.read_int(48), -0x3c49ba00)
		self.assertEqual(self.f.read_int(49), -((~0xb64600aa+1) % (2**32)))
		self.assertEqual(self.f.read_int(50), 0x4600aa46)
		self.assertEqual(self.f.read_int(51), 0x00aa4647)
		self.assertEqual(self.f.read_int(52), -((~0xaa464748+1) % (2**32)))
		self.assertEqual(self.f.read_int(53), 0x46474849)

	def test_read_int_spill(self):
		with self.assertRaisesRegex(hprof.EofError, 'read.*55:59.*57'):
			self.f.read_uint(55)

	def test_read_int_outside(self):
		with self.assertRaisesRegex(hprof.EofError, '2000.*57'):
			self.f.read_uint(2000)

	def test_read_int_negative(self):
		with self.assertRaisesRegex(hprof.EofError, '-2'):
			self.f.read_uint(-2)


class TestAsciiReads(TestCase):
	def setUp(self):
		self.f = hprof.HprofFile(inputfile)

	def tearDown(self):
		self.f.close()

	def test_read_ascii_fixed1(self):
		self.assertEqual(self.f.read_ascii(40, 1), 'A')
		self.assertEqual(self.f.read_ascii(41, 1), 'B')
		self.assertEqual(self.f.read_ascii(42, 1), 'C')
		self.assertEqual(self.f.read_ascii(43, 1), 'D')
		self.assertEqual(self.f.read_ascii(44, 1), '\0')

	def test_read_ascii_fixed2(self):
		self.assertEqual(self.f.read_ascii(40, 2), 'AB')
		self.assertEqual(self.f.read_ascii(41, 2), 'BC')
		self.assertEqual(self.f.read_ascii(42, 2), 'CD')
		self.assertEqual(self.f.read_ascii(43, 2), 'D\0')

	def test_read_ascii_fixed3(self):
		self.assertEqual(self.f.read_ascii(40, 3), 'ABC')
		self.assertEqual(self.f.read_ascii(41, 3), 'BCD')
		self.assertEqual(self.f.read_ascii(42, 3), 'CD\0')

	def test_read_ascii_fixed4(self):
		self.assertEqual(self.f.read_ascii(40, 4), 'ABCD')
		self.assertEqual(self.f.read_ascii(41, 4), 'BCD\0')
		self.assertEqual(self.f.read_ascii(42, 4), 'CD\0\0')

	def test_read_ascii_fixed5(self):
		self.assertEqual(self.f.read_ascii(40, 5), 'ABCD\0')
		self.assertEqual(self.f.read_ascii(41, 5), 'BCD\0\0')

	def test_read_terminated_ascii(self):
		self.assertEqual(self.f.read_ascii(40), 'ABCD')
		self.assertEqual(self.f.read_ascii(41), 'BCD')
		self.assertEqual(self.f.read_ascii(42), 'CD')
		self.assertEqual(self.f.read_ascii(43), 'D')
		self.assertEqual(self.f.read_ascii(44), '')
		self.assertEqual(self.f.read_ascii(45), '')

	def test_read_invalid_ascii(self):
		with self.assertRaises(UnicodeError):
			self.f.read_ascii(48)

	def test_read_ascii_fixed_spill(self):
		with self.assertRaisesRegex(hprof.EofError, 'read.*55:65.*57'):
			self.f.read_ascii(55,10)

	def test_read_ascii_fixed_outside(self):
		with self.assertRaisesRegex(hprof.EofError, '60.*57'):
			self.f.read_ascii(60, 2)

	def test_read_ascii_fixed_negative(self):
		with self.assertRaisesRegex(hprof.EofError, '-1'):
			self.f.read_ascii(-1, 1)

	def test_read_ascii_fixed_negative_len(self):
		with self.assertRaisesRegex(ValueError, '-2'):
			self.f.read_ascii(43, -2)

	def test_read_terminated_ascii_spill(self):
		with self.assertRaisesRegex(hprof.EofError, 'read.*55.*term.*57'):
			self.f.read_ascii(55)

	def test_read_terminated_ascii_outside(self):
		with self.assertRaisesRegex(hprof.EofError, '60.*57'):
			self.f.read_ascii(60)

	def test_read_terminated_ascii_negative(self):
		with self.assertRaisesRegex(hprof.EofError, '-4'):
			self.f.read_ascii(-4)

class TestUtf8Reads(TestCase):
	def setUp(self):
		self.f = hprof.HprofFile(inputfile)

	def tearDown(self):
		self.f.close()

	def test_read_utf8_fixed1(self):
		self.assertEqual(self.f.read_utf8(40, 1), 'A')
		self.assertEqual(self.f.read_utf8(41, 1), 'B')
		self.assertEqual(self.f.read_utf8(42, 1), 'C')
		self.assertEqual(self.f.read_utf8(43, 1), 'D')
		self.assertEqual(self.f.read_utf8(44, 1), '\0')

	def test_read_utf8_fixed2(self):
		self.assertEqual(self.f.read_utf8(40, 2), 'AB')
		self.assertEqual(self.f.read_utf8(41, 2), 'BC')
		self.assertEqual(self.f.read_utf8(42, 2), 'CD')
		self.assertEqual(self.f.read_utf8(43, 2), 'D\0')

	def test_read_utf8_fixed3(self):
		self.assertEqual(self.f.read_utf8(40, 3), 'ABC')
		self.assertEqual(self.f.read_utf8(41, 3), 'BCD')
		self.assertEqual(self.f.read_utf8(42, 3), 'CD\0')

	def test_read_utf8_fixed4(self):
		self.assertEqual(self.f.read_utf8(40, 4), 'ABCD')
		self.assertEqual(self.f.read_utf8(41, 4), 'BCD\0')
		self.assertEqual(self.f.read_utf8(42, 4), 'CD\0\0')

	def test_read_utf8_fixed5(self):
		self.assertEqual(self.f.read_utf8(40, 5), 'ABCD\0')
		self.assertEqual(self.f.read_utf8(41, 5), 'BCD\0\0')

	def test_read_swedish_utf8(self):
		self.assertEqual(self.f.read_utf8(48, 3), 'öF')

	def test_read_incomplete_utf8(self):
		with self.assertRaises(UnicodeError):
			self.f.read_utf8(49, 2)

	def test_read_truncated_utf8(self):
		with self.assertRaises(UnicodeError):
			self.f.read_utf8(48, 1)

	def test_read_utf8_fixed_spill(self):
		with self.assertRaisesRegex(hprof.EofError, 'read.*55:65.*57'):
			self.f.read_utf8(55,10)

	def test_read_utf8_fixed_outside(self):
		with self.assertRaisesRegex(hprof.EofError, '60.*57'):
			self.f.read_utf8(60, 2)

	def test_read_utf8_fixed_negative(self):
		with self.assertRaisesRegex(hprof.EofError, '-1'):
			self.f.read_utf8(-1, 1)

	def test_read_utf8_fixed_negative_len(self):
		with self.assertRaisesRegex(ValueError, '-2'):
			self.f.read_utf8(43, -2)
