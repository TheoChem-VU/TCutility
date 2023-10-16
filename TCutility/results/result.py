'''Module containing the TCutility.results.result.Result class.'''


class Result(dict):
    '''Class used for storing results from AMS calculations. The class is functionally a dictionary, but allows dot notation to access variables in the dictionary. 
    The class works case-insensitively, but will retain the case of the key when it was first set.'''
    def __repr__(self):
        if not self:
            return 'Result(empty)'
        else:
            return 'Result'

    def __call__(self):
        head, method = '.'.join(self.get_parent_tree().split('.')[:-1]), self.get_parent_tree().split('.')[-1]
        raise AttributeError(f'Tried to call method "{method}" from {head}, but {head} is empty')

    def __getitem__(self, key):
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
        # Custom method to check if the key is defined in this object, case-insensitive.
        return key.lower() in [key_.lower() for key_ in self.keys()]

    def __hash__(self):
        raise KeyError(f'Tried to hash {self.get_parent_tree()}, but it is empty')

    def get_parent_tree(self):
        if '__parent__' not in self:
            return 'Head'
        parent_names = self.__parent__.get_parent_tree()
        parent_names += '.' + self.__name__
        return parent_names

    def __set_empty(self, key):
        # This function checks if the key has been set. 
        # If it has not, we create a new Result object and set it at the desired key
        if key not in self:
            val = Result()
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


if __name__ == '__main__':
    ret = Result()

    ret.adf.x = {'a': 1, 'b': 2}
    test_dict = {}
    # test_dict[ret.adf.y] = 20
    # ret.adf.y.join()
    # {ret.test: 123}
    ret.__name = 'testname'
    print(ret.__name)
    print(ret.adf.y)
