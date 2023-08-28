'''Module containing the TCutility.results.result.Result class.'''


class Result(dict):
    '''Class used for storing results from AMS calculations. The class is functionally a dictionary, but allows dot notation to access variables in the dictionary.'''
    def __getattr__(self, key):
        if key not in self:
            val = Result()
            self.__setitem__(key, val)
            return val
            
        val = self.__getitem__(key)
        if isinstance(val, dict):
            val = Result(val)
            self.__setattr__(key, val)
        return val

    def __getitem__(self, key):
        if key not in self:
            val = Result()
            self.__setitem__(key, val)
            return val
        return super().__getitem__(key)

    def __setattr__(self, key, val):
        self.__setitem__(key, val)
