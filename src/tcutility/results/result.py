'''Module containing the TCutility.results.result.Result class.'''
import dictfunc
import sys


class Result(dict):
    '''Class used for storing results from AMS calculations. The class is functionally a dictionary, but allows dot notation to access variables in the dictionary. 
    The class works case-insensitively, but will retain the case of the key when it was first set.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # if we are casting an object to a Result object
        # we will copy all data to this one and all dictionaries will be turned into Result object
        # turn every value into a Result object if possible
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = Result(value)
            else:
                self[key] = value

    def __call__(self):
        '''Calling of a dictionary subclass should not be possible, instead we raise an error with information about the key and method that were attempted to be called.'''
        head, method = '.'.join(self.get_parent_tree().split('.')[:-1]), self.get_parent_tree().split('.')[-1]
        raise AttributeError(f'Tried to call method "{method}" from {head}, but {head} is empty')

    def __str__(self):
        '''Override str method to prevent printing of hidden keys. You can still print them if you call repr instead of str.'''
        return '{' + ', '.join([f'{key}: {str(val)}' for key, val in self.items()]) + '}'

    def items(self):
        '''We override the items method from dict in order to skip certain keys. We want to hide keys starting and ending
        with dunders, as they should not be exposed to the user.
        '''
        return [(key, self[key]) for key in self.keys()]

    def keys(self):
        original_keys = super().keys()
        return [key for key in original_keys if not (key.startswith('__') and key.endswith('__'))]

    def multi_keys(self):
        '''
        Return multi_keys for this Result object. These are unnested keys that can be used if you want a flattened Result object.
        '''
        def dict_to_list(a):
            '''
            Return a nested dictionary as a list of keys and values.
            '''
            lst = []
            if not isinstance(a, dict):
                return [[a]]
            for k, v in a.items():
                if isinstance(v, dict):
                    if v == {}:
                        lst.append([k, {}])
                    else:
                        [lst.append([k, *x]) for x in dict_to_list(v)]
                else:
                    lst.append([k, v])
            return lst

        # cast this object to a list of keys and values
        mks = dict_to_list(self)
        # write the multi-keys separated with dots
        mks = ['.'.join(mk[:-1]) for mk in mks]
        return mks

    def __getitem__(self, key):
        if key.startswith('__') and key.endswith('__'):
            return None
        self.__set_empty(key)
        val = super().__getitem__(self.__get_case(key))
        return val

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __setitem__(self, key, val):
        # we set the item, but if it is a dict we convert the dict to a Result first
        if isinstance(val, dict):
            val = Result(val)
        super().__setitem__(self.__get_case(key), val)

    def __setattr__(self, key, val):
        self.__setitem__(key, val)

    def __contains__(self, key):
        # Custom method to check if the key is defined in this object and is also non-empty, case-insensitive.
        return key.lower() in [key_.lower() for key_ in self.keys()] and self[key]

    def __hash__(self):
        '''Hashing of a dictionary subclass should not be possible, instead we should raise an error to let the user know
        that they made a mistake. Also give information of which key was being read.
        '''
        raise KeyError(f'Tried to hash {self.get_parent_tree()}, but it is empty')

    def __reduce__(self):
        return 'TCutility.results.result.Result'

    def __bool__(self):
        '''Make sure that keys starting and ending in "__" are skipped'''
        return len([key for key in self.keys() if not (key.startswith('__') and key.endswith('__'))]) > 0

    def __sizeof__(self):
        '''
        Magic method used by `sys.getsizeof <https://docs.python.org/3/library/sys.html#sys.getsizeof>`_ to determine the memory footprint of this object.
        '''
        s = super().__sizeof__()
        for key in self.multi_keys():
            s += sys.getsizeof(self.get_multi_key(key))
        return s

    def getsizeof(self):
        '''
        Return the size of this object in bytes.
        '''
        return self.__sizeof__()

    def get_parent_tree(self):
        '''Method to get the path from this object to the parent object. The result is presented in a formatted string'''
        # every parent except the top-most parent has defined a __parent__ attribute
        if '__parent__' not in self:
            return 'Head'
        # iteratively build the tree using the __name__ attribute.
        parent_names = self.__parent__.get_parent_tree()
        parent_names += '.' + self.__name__
        return parent_names

    def __set_empty(self, key):
        # This function checks if the key has been set. 
        # If it has not, we create a new Result object and set it at the desired key
        if self.__get_case(key) not in self.keys():
            val = Result()
            # we also keep track of the parent of this object and also the name it was assigned to for later bookkeeping
            val.__parent__ = self
            val.__name__ = key
            self.__setitem__(key, val)

    def __get_case(self, key):
        # Get the case of the key as it has been set in this object.
        # The first time a key-value pair has been assigned the case of the key will be set.
        for key_ in self:
            if key_.lower() == key.lower():
                return key_
        return key

    def prune(self):
        '''Remove empty paths of this object.
        '''
        items = list(self.items())
        for key, value in items:
            try:
                value.prune()
            except AttributeError:
                pass

            if not value:
                del self[key]

    def get_multi_key(self, key: str):
        '''
        Method that returns the value of a "multikey". The multikey is multiple keys joined by dots. 
        E.g. res.properties.energy.bond can be gotten by calling res.get_multi_key("properties.energy.bond")
        '''
        data = self
        for keypart in key.split('.'):
            data = data[keypart]
        return data

    def as_plams_settings(self):
        '''
        Returns this Result object as a plams.Settings object.
        '''
        from scm import plams
        import dictfunc

        clean_dict = dictfunc.list_to_dict(dictfunc.dict_to_list(self))
        return plams.Settings(clean_dict)

    def copy(self):
        import copy

        # cast this object to a list of keys and values
        lsts = dictfunc.dict_to_list(self)
        # copy everthing in the lists
        lsts = [[copy.copy(x) for x in lst] for lst in lsts]
        # and return a new result object
        return Result(dictfunc.list_to_dict(lsts))


if __name__ == '__main__':
    ret = Result()
    # print(ret.adf)
    # print(dict(ret.adf))
    # print(bool(ret.adf))
    ret.adf.x = {'a': 1, 'b': 2}
    # ret.adf.system.atoms = []
    # ret.adf.system.atoms.append('test 1 2 3')

    # test_dict[ret.adf.y] = 20
    # ret.adf.y.join()
    # {ret.test: 123}
    # ret.__name__ = 'testname'
    # print(ret.__name__)
    print(repr(ret))
