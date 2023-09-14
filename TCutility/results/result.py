'''Module containing the TCutility.results.result.Result class.'''


class Result(dict):
    '''Class used for storing results from AMS calculations. The class is functionally a dictionary, but allows dot notation to access variables in the dictionary.'''
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
        if key not in self:
            val = Result()
            self.__setitem__(key, val)
            return val
        return super().__getitem__(key)

    def __setattr__(self, key, val):
        self.__setitem__(key, val)
    def __get_case(self, key):
        # Get the case of the key as it has been set in this object.
        # The first time a key-value pair has been assigned the case of the key will be set.
        for key_ in self:
            if key_.lower() == key.lower():
                return key_
        return key
