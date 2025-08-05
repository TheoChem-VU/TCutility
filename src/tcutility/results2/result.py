from typing import Tuple, Any


class NestedDict(dict):
	def __init__(self, data=None):
		self._priorities = {}
		super().__init__(data or {})

	def set(self, *args: Tuple[Any], priority: float = 0):
		'''
		Override of the standard ``dict.set`` method allowing 
		for setting a nested key in one call.
	
		Args:
			*args: an unpacked tuple of firstly keys and then the value to be set.
			priority: the priority for setting this value. If the given priority 
				is higher than a previously set priority we set the value, 
				otherwise we ignore it.

		Examples:
			.. code-block:: python

				>>> nd = NestedDict()
				>>> nd.set('a', 'b', 'c', 15, priority=1)
				>>> nd
				{'a': {'b': {'c': 15}}}
				>>> nd.set('a', 'b', 'c', 'overwritten?', priority=0)
				>>> nd
				{'a': {'b': {'c': 15}}}
				>>> nd.get('a', 'b', 'c')
				15
		'''
		keys, val = args[:-1], args[-1]

		if self._priorities.get(keys, 0) > priority:
			return

		self._priorities[keys] = priority

		d = self
		for i, key in enumerate(keys):
			d.setdefault(key, {})
			if i == len(keys) - 1:
				d[key] = val
			else:
				d = d[key]

	def get(self, *keys: Tuple[Any]) -> Any:
		'''
		Get a nested value from this dict.

		Args:
			*keys: an unpacked tuple of keys used to access the value.

		Example:
			.. code-block:: python

				>>> nd = NestedDict()
				>>> nd.set('a', 'b', 'c', 15, priority=1)
				>>> nd
				{'a': {'b': {'c': 15}}}
				>>> nd.get('a', 'b')
				{'c': 15}
				>>> nd.get('a', 'b', 'c')
				15
		'''
		d = self
		for key in keys:
			if key not in d:
				return
			d = d[key]
		return d


if __name__ == '__main__':
	nd = NestedDict()
	nd.set('a', 'b', 'c', 15)
	print(nd)
	print(nd.get('a','b'))