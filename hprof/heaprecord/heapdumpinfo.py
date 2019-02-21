#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord
from ..errors import *
from ..offset import AutoOffsets, idoffset

offsets = AutoOffsets(1,
	'TYPE', 4,
	'NAME', idoffset(1),
	'END')

class HeapDumpInfo(HeapRecord):
	HPROF_DUMP_TAG = 0xfe

	@property
	def type(self):
		return self._hprof_uint(offsets.TYPE)

	@property
	def name(self):
		nameid = self._hprof_id(offsets.NAME)
		return self.hprof_file.name(nameid)

	def __len__(self):
		return offsets.END.flatten(self.hprof_file.idsize)

	def __str__(self):
		return 'HeapDumpInfo(type=%d name=%s)' % (self.type, self.name)
