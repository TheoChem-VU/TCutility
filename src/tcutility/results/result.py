'''Module containing the TCutility.results.result.Result class.'''
import dictfunc
from typing import Union, Any, List
from tcutility import ensure_list


class ResultInspector:
    '''
    Utility class for getting values from Result objects.
    This allows us to inspect the Result object without accidentally setting keys in it.
    '''
    __private__ = ['__parent__', '__key__', '__result__', '__isroot__']
    def __init__(self, parent: Union['ResultInspector', 'Result'], key: str, is_root: bool = False):
        self.__parent__ = parent
        self.__key__ = key
        self.__result__ = None
        self.__isroot__ = is_root

    def __getattr__(self, key: str) -> 'ResultInspector':
        return ResultInspector(self, key)

    #### add multiple arguments to access things
    def __getitem__(self, key: str) -> 'ResultInspector':
        return self.__getattr__(key)

    def __setattr__(self, key: str, value: Any):
        '''
        We overload __setattr__ to be able to propagate the values upstream to the root
        '''
        # we still should be able to use the default setattr functionality:
        super().__setattr__(key, value)
        # but if the key is not in the predetermined __private__ keys we do something extra
        if key in self.__private__:
            return

        # we store the result
        self.__result__ = Result()
        self.__result__[key] = value
        self.propagate_value()
        self = self.__result__

    def __setitem__(self, key: str, value: Any):
        self.__setattr__(key, value)

    def __contains__(self, key: str):
        return False

    def propagate_value(self):
        '''
        If we are ready we can define the tree on the root Result object with the correct values.
        The full tree of objects of this class will be destroyed by the garbage collector afterwards.
        '''
        # if we are at the root we can set the key/value on the Result object directly
        if self.__isroot__:
            self.__parent__[self.__key__] = self.__result__
            return

        # otherwise we create a new Result object on the parent that we will propagate upwards
        self.__parent__.__result__ = Result()
        # assign the key/value on this intermediate Result object
        self.__parent__.__result__[self.__key__] = self.__result__
        # and then propagate the parent until we reach the root
        self.__parent__.propagate_value()

    def __bool__(self):
        return False

    def __repr__(self):
        return 'None'

    def __str__(self):
        return 'None'

    def __eq__(self, other: Any):
        '''
        This class mimics None, so equality operator should only
        # be True if other is None
        '''
        return other is None

    def __call__(self, *args, **kwargs):
        '''
        If this object gets called it means there was an attempt to call a method of the parent object.
        This is not allowed (since the parent is not a valid object), so we raise a descriptive error for the user.
        '''
        raise AttributeError(f'"Result().{self.path_to_root[:-len(self.__key__)+1]}" does not have a method named ".{self.__key__}".')

    @property
    def path_to_root(self) -> str:
        '''
        Return a string of the full path from the root to this object.
        '''
        parts = [self.__key__]
        curr_obj = self
        while not curr_obj.__isroot__:
            curr_obj = curr_obj.__parent__
            parts.append(curr_obj.__key__)
        return '.'.join(parts[::-1])


class Result(dict):
    '''
    Sub-class of built-in dict that supports dot-notation for accessing and setting values in this object.
    Furthermore, keys are case-insensitive and the class allows accessing via multi-keys for ease of use.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = Result(value)

    def __getattr__(self, *key: List[str]) -> Any:
        # we override this so that we can use dot-notation to access values in this object

        # keys can be given multiple at a time
        # In that case we make the keys into a multikey before accessing
        key = ":".join(ensure_list(key[0]))
        # get the value of the key. This key can be 
        # any case and can also be a multikey
        # flattening grants support for multikeys
        flat = self.flattened(True)
        # match_case grants support for case-insensitivity
        val = flat.get(self.match_case(key))

        # if the value is None we have to do something special
        if val is not None:
            return val

        # likely we are trying to access a value that does not exist in this
        # object, so we should instead inspect it. this way we are not adding
        # unnecessary keys to this object due to accessing them
        return ResultInspector(self, key, is_root=True)

    def __setattr__(self, key: str, value: Any):
        # override this so that we can use dot-notation for setting values
        self.__setitem__(key, value)

    def __getitem__(self, *key: List[str]) -> Any:
        # point this to __getattr__ so that the keys are parsed correctly
        return self.__getattr__(*key)

    def __setitem__(self, *key: List[str]):

        value = key[-1]
        key = ":".join(ensure_list(key[0]))
        key_parts = key.split(':')

        if len(key_parts) == 1:
            super().__setitem__(key_parts[-1], value)
            return

        inspector = self
        for part in key_parts[:-1]:
            inspector = inspector[part]
        inspector[key_parts[-1]] = value

    def __contains__(self, key: str) -> bool:
        # we override this to make it case-insensitive
        # and also so that it works with mutli-keys
        return self.match_case(key) in self.multi_keys(True)

    def match_case(self, key: str) -> str:
        '''
        Parse key such that it matches the case that was originally set in this Result object.

        Example:
            >>> r = Result()
            >>> r.AdF.settings.functional = 'BLYP-D3'
            >>> r.match_case('adf')
            AdF
            >>> r.match_case('ADF:SETTINGS:FUNCTIONAL')
            AdF.settings.functional
        '''
        # first get a dictionary of lowered keys mapping to the original keys
        # for the keys and multikeys currently set in this object
        lowered = {key.lower(): key for key in self.multi_keys(True)}
        # then simply access it or return the given key if it is not present
        return lowered.get(key.lower(), key)

    def multi_keys(self, include_intermediates: bool = False) -> List[str]:
        '''
        Get multi-keys of this Result object. These keys will point to unnested values.
        Multi-keys are separate keys that are separated by `:` characters.

        Args:
            include_intermediates: whether to include intermediate multi-keys. 
                Enabling this option will return all in-between keys, so not only the endpoints.
                If enabled, the keys will not always point to unnested values, but could point to nested Result objects.

        Returns:
            A list of multi-keys that can be used to access values in this Result object.
            If intermediates are included this method will return a list of all accessible positions in the tree.

        Example:

            .. code-block:: python

                >>> res.a.b.c = 10
                >>> res['a:b:c']
                10
                >>> res.a.b.c
                10
                >>> res['a:b']
                {c: 10}
        '''
        lsts = dictfunc.dict_to_list(self)
        if include_intermediates:
            return [':'.join(lst[:-i]) for lst in lsts for i in range(1, len(lst))]
        else:
            return [':'.join(lst[:-1]) for lst in lsts]

    def flattened(self, include_intermediates: bool = False) -> dict:
        '''
        Return this Result object as a flattened dictionary.
        This will be an unnested dictionary with the multikeys and their values.

        Args:
            include_intermediates: whether to include intermediate multi-keys. Default is False.

        Returns:
            An unnested dictionary with multi-keys as the key and their values as the value. 
        '''
        flattened = {}
        # each entry in flattened will be a multikey
        for key in self.multi_keys(include_intermediates):
            # get the value of the multikey
            parts = key.split(':')
            # iterative go down this result object to reach the multikey
            res = self
            for part in parts:
                res = res.get(part)
            flattened[key] = res

        return flattened

    def asdict(self) -> dict:
        '''
        Return this Result object as a dictionary. 
        This can be useful if you need pure Python classes.

        Returns:
            This Result object converted to built-in dictionary class.
        '''
        ret = {}
        # get all multikeys that are at the leaves
        # we exclude intermediates here so that we dont overwrite a deeper key later on
        for key in self.multi_keys(False):
            curr_d = ret
            # split the multikey into parts
            # and assign empty dicts until you get to the last part
            parts = key.split(':')
            for part in parts[:-1]:
                curr_d = curr_d.setdefault(part, {})
            # the last part is the name of the final key, so we will set it to the value
            curr_d[parts[-1]] = self[key]
        return ret


if __name__ == '__main__':
    res = Result()
    # res.a.b.c = 10
    # print(res.a.b.c)
    res['a:b:c'] = 10
    # print(res['a:b'])
    # print(res['a', 'b', 'c'])
    res['a', 'b', 'c'] = 11
    print(res)
    # print(res['a', 'b', 'c'])
