from ._heaprecord import Allocation

from .._errors import FieldNotFoundError
from .._offset import offset, AutoOffsets, idoffset
from .._types import JavaType


class Object(Allocation):
	'''A normal object instance on the heap (i.e. not a Class or an array).

	Members:
	hprof_file -- the HprofFile this object belongs to.
	hprof_addr -- the byte address of this object in hprof_file.
	hprof_heap -- the hprof.Heap this object belongs to.
	'''

	HPROF_DUMP_TAG = 0x21

	_hprof_offsets = AutoOffsets(1,
		'ID',       idoffset(1),
		'STRACE',   4,
		'CLSID',    idoffset(1),
		'DATASIZE', 4,
		'DATA'
	)

	@property
	def hprof_class_id(self):
		'''the ID of this object's class.'''
		return self._hprof_id(self._hproff.CLSID)

	@property
	def _hprof_len(self):
		return self._hproff.DATA + self._hprof_uint(self._hproff.DATASIZE)

	def __str__(self):
		cid = self.hprof_class_id
		cname = self.hprof_file.get_class_info(cid).class_name
		cname = cname.rsplit('.', 1)[-1]
		return '%s(id=0x%x)' % (cname, self.hprof_id)

	def __repr__(self):
		sid = self.hprof_id
		cid = self.hprof_class_id
		cname = self.hprof_file.get_class_info(cid).class_name
		return 'Object(class=%s, id=0x%x)' % (cname, sid)
