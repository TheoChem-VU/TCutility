'''
Tiny module that handles caching rkf files. 
rkf files take a long time to open (especially {engine}.rkf), so it is better to open them once and cache them for later use
'''
from scm import plams

# the actual cache is stored in this dict
_cache = {}

def store(reader):
	# store an rkf reader in the cache
	# it can later be indexed by its path
	path = reader.path
	_cache[path] = reader

def get(path):
	# get an rkf reader from the cache

	# if the path is already in the cache, simply return it
	if path in _cache:
		return _cache[path]
	# else we will load the rkf file and store it in the cache
	reader = plams.KFReader(path)
	store(reader)
	return reader

def unload(arg):
	# arg can either be a path or reader object
	# since rkf files can be quite large, we should not forget to unload
	# them after we have finished reading from them

	# if the arg is a key in the cache we will delete the key
	if arg in _cache:
		del _cache[arg]
		return
	# if it is not a key, find the key corresponding to the value and delete it
	if arg in _cache.values():
		key = [key for key, val in _cache.items() if val == arg][0]
		del _cache[key]
		return
