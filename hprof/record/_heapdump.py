#!/usr/bin/env python3
#coding=utf8

from . import _base

from .. import heap
from .._errors import *

class HeapDumpSegment(_base.Record):
	TAG = 28

	def __str__(self):
		return 'HeapDumpSegment(payloadsize=%s)' % (len(self) - _base.offsets.BODY)

	def records(self):
		offset = _base.offsets.BODY
		end = len(self)
		while offset < end:
			r = heap.create(self.hprof_file, self.hprof_addr + offset)
			offset += len(r)
			if offset > end:
				raise FileFormatError('subrecord ends at 0x%x, dump segment ends at 0x%x' % (offset, end))
			yield r

class HeapDumpEnd(_base.Record):
	TAG = 44
