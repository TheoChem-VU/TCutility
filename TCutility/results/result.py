'''Module containing the TCutility.results.result.Result class.'''


class Result(dict):
    '''Class used for storing results from AMS calculations. The class is functionally a dictionary, but allows dot notation to access variables in the dictionary. The class works case-insensitively, but will retain the case of the key when it was first set.'''
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

    def __set_empty(self, key):
        # This function checks if the key has been set. 
        # If it has not, we create a new Result object and set it at the desired key
        if key not in self:
            val = Result()
            self.__setitem__(key, val)

    def __get_case(self, key):
        # Get the case of the key as it has been set in this object.
        # The first time a key-value pair has been assigned the case of the key will be set.
        for key_ in self:
            if key_.lower() == key.lower():
                return key_
        return key


if __name__ == '__main__':
    ret = Result()
    ret.aDf.x = {'a': 1, 'b': 2}
    print(ret.adf.x.a)

    ret.ADF.y = 2345
    ret.dftb.z = 'hello'
    print(ret)
