def any(iterable):
    for elem in iterable:
        if elem:
            return True
    return False

def all(iterable):
    for elem in iterable:
        if not elem:
            return False
    return True

def sum(iterable, start=0):
    for elem in iterable:
        start += elem
    return start

def zip(*args):
    iterators = [iter(arg) for arg in args]
    result = []
    while_true:
        try:
            item = [iterator.next() for iterator in iterators]
        except StopIteration:
            return result
        result.append(item)

def min(*iterable):
    value = None # bad
    for elem in iterable:
        if value is None or elem < value:
            value = elem
    return value

def isinstance(x, class_):
    return getattr(x, "__class__") == class_

class object:
    def __pnew__(cls, *args):
        self = Instance(cls.__name__)
        self.__type__ = cls.__name__
        self.__path__ = cls.__path__
        self.__class__ = cls
        self.__pinit__(*args)
        return self

    def __pinit__(self, *args):
        pass

    def __nonzero__(self):
        return False

    __bool__ = __nonzero__

class Singleton(object):
    def __pinit__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    __str__ = __repr__

class Int(object):
    def __pinit__(self, value=0):
        self.value = value

    def __padd__(self, other):
        return Int(self.value + other.value)

    def __nonzero__(self):
        return self.value != 0

    __bool__ = __nonzero__

class Bool(Int):
    def __pnew__(cls, value=0):
        object.__pnew__(cls)
        if value:
            return True
        else:
            return False

    def __repr__(self):
        if self.value:
            return "True"
        else:
            return "False"

    __str__ = __repr__

    def __and__(self, other):
        if isinstance(other, Bool):
            return Bool(int(self) & int(other))
        else:
            return int.__and__(self, other)

    __rand__ = __and__

    def __or__(self, other):
        if isinstance(other, Bool):
            return Bool(int(self) | int(other))
        else:
            return int.__or__(self, other)

    __ror__ = __or__

    def __xor__(self, other):
        if isinstance(other, Bool):
            return Bool(int(self) ^ int(other))
        else:
            return int.__xor__(self, other)

    __rxor__ = __xor__

False = Int.__pnew__(Bool, 0)
True = Int.__pnew__(Bool, 1)

class ListIterator(object):
    def __pinit__(self, iterable):
        self._error = False
        self.iterable = iterable
        self.index = -1

    def next(self):
        if self._error:
            raise StopIteration()
        self.index += 1
        try:
            return self.iterable[self.index]
        except IndexError:
            self._error = True
            raise StopIteration()

    def __iter__(self):
        return self

class List(object):
    def __pinit__(self, value=None):
        self.max_length = 4
        self._content = c_array(self.max_length)
        self.length = 0
        if value is not None:
            self.extend(value)

    def increase_to(self, new_length):
        if self.max_length >= new_length:
            self.length = new_length
            return
        while self.max_length < new_length:
            self.max_length *= 2
        new_content = c_array(self.max_length)
        for index in xrange(self.length):
            new_content[index] = self._content[index]
        self._content = new_content
        self.length = new_length

    def decrease_to(self, new_length):
        if self.max_length <= 4 * new_length:
            self.length = new_length
            return
        while self.max_length > 2 * new_length + 2:
            self.max_length /= 2
        new_content = c_array(self.max_length)
        for index in xrange(self.length):
            new_content[index] = self._content[index]
        self._content = new_content
        self.length = new_length

    def append(self, elem):
        self.increase_to(self.length + 1)
        self._content[self.length - 1] = elem

    def extend(self, iterable):
        # Iterable length may not be known in advance...
        for elem in iterable:
            self.append(elem)

    def insert(self, index, item):
        self.increase_to(self.length + 1)
        # Should make only one copy on increase instead of 2
        for i in xrange(self.length - 2, index - 1, -1):
            self._content[i + 1] = self._content[i]
        self._content[index] = item

    def __checkindex__(self, index):
        if index < 0:
            index = self.length + index
        if index >= self.length or index < 0:
            raise IndexError("List index out of range")
        return index

    def __getitem__(self, index):
        # Putting this in getitem creates an infinite loop since if calls getitem
        if type(index) == _slice:
            return self.__getslice__(index.start, index.stop, index.step)
        index = self.__checkindex__(index)
        return self._content[index]

    def __setitem__(self, index, value):
        index = self.__checkindex__(index)
        self._content[index] = value

    def pop(self, index=None):
        if index is None:
            index = self.length - 1
        index = self.__checkindex__(index)
        item = self._content[index]
        # Should make only one copy on decrease instead of 2
        self.decrease_to(self.length - 1)
        for i in xrange(index, self.length):
            self._content[i] = self._content[i + 1]
        return item

    def remove(self, item):
        self.pop(self.index(item))

    def reverse(self):
        for i in xrange(self.length / 2):
            self._content[i], self._content[self.length-1-i] = self._content[self.length-1-i], self._content[i]

    def __iter__(self):
        return ListIterator(self)

    def __len__(self):
        return self.length

    def __nonzero__(self):
        return self.length > 0

    __bool__ = __nonzero__

    def __contains__(self, item):
        for elem in self:
            if elem == item:
                return True
        return False

    def __getslice__(self, start, stop, step=1):
        new_slice = List()
        for index in xrange(start, stop, step):
            new_slice.append(self._content[index])
        return new_slice

    def __setslice__(self, start, stop, value):
        i = start
        for elem in value:
            print elem
            if i < self.length:
                self._content[i] = elem
            else:
                self.append(elem)
            i += 1
            if i == stop:
                break

    def __eq__(self, other):
        return len(self) == len(other) and any(self[i] == other[i]
                                               for i in xrange(self.length))

    def __ne__(self, other):
        return len(self) != len(other) or any(self[i] != other[i]
                                              for i in xrange(self.length))

    # Doesn't work if other is not indexable!
    def __lt__(self, other):
        for i in xrange(min(len(self), len(other))):
            if self[i] != other[i]:
                return self[i] < other[i]
        return len(self) < len(other)

    def __gt__(self, other):
        for i in xrange(min(len(self), len(other))):
            if self[i] != other[i]:
                return self[i] < other[i]
        return len(self) < len(other)

    def index(self, item):
        for index in xrange(self.length):
            if item == self._content[index]:
                return index
        raise ValueError("Item not found in List")

    def count(self, item):
        return sum(elem == item for elem in self)

    def __add__(self, other):
        new_list = List(self)
        new_list.extend(other)
        return new_list

    def __repr__(self):
        s = "["
        for index in xrange(self.length):
            s += repr(self._content[index])
            if index != (self.length - 1):
                s += ", "
        s += "]"
        return s

    __str__ = __repr__

class _NoKey(object):
    pass

NoKey = _NoKey()
KeyErrorSingleton = Singleton("KeyErrorSingleton")

class Dict(object):
    def __pinit__(self, __initial__=None):
        self.clear()
        if __initial__ is not None:
            self.update(__initial__)

    def clear(self):
        self.size = 10
        self.__keys__ = c_array(self.size)
        for i in xrange(self.size):
            self.__keys__[i] = NoKey
        self.__values__ = c_array(self.size)
        for i in xrange(self.size):
            self.__values__[i] = NoKey
        self.length = 0

    def getindex(self, key):
        # self.size is always a power of 2?
        hash_value = hash(key)
        while_true:
            index = hash_value % self.size
            if self.__keys__[index] == key or self.__keys__[index] is NoKey:
                return index
            hash_value = 5*hash_value % 1000000

    def increase_to(self, new_length):
        if new_length <= 3 * self.size/4:
            self.length = new_length
            return
        old_size = self.size
        while new_length >= 3 * self.size/4:
            self.size *= 2
        old_keys = self.__keys__
        old_values = self.__values__
        new_keys = c_array(new_length)
        new_values = c_array(new_length)
        for index in xrange(old_size):
            if old_keys[index] is not NoKey:
                new_index = self.getindex(old_keys[index])
                self.__keys__[new_index] = old_values[index]

    def __getitem__(self, key):
        index = self.getindex(key)
        if self.__keys__[index] == key:
            return self.__values__[index]
        raise KeyError(str(key))

    def __setitem__(self, key, value):
        index = self.getindex(key)
        if self.__keys__[index] is NoKey:
            self.__keys__[index] = key
            self.increase_to(self.length + 1)
        self.__values__[index] = value

    def __contains__(self, key):
        return self.__keys__[self.getindex(key)] == key

    def get(self, key, default=None):
        index = self.getindex(key)
        if self.__keys__[index] == key:
            return self.__values__[index]
        return default

    def __iter__(self):
        return ListIterator(self.keys())

    def keys(self):
        return [self.__keys__[i] for i in xrange(self.size)
                if self.__keys__[i] is not NoKey]

    def values(self):
        return [self.__values__[i] for i in xrange(self.size)
                if self.__keys__[i] is not NoKey]

    def items(self):
        return [(self.__keys__[i], self.__values__[i]) for i in xrange(self.size)
                if self.__keys__[i] is not NoKey]

    def update(self, other):
        for k in other:
            self[k] = other[k]

    def setdefault(self, key, value=None):
        index = self.getindex(key)
        if self.__keys__[index] is NoKey:
            self.__keys__[index] = key
            self.increase_to(self.length + 1)
            self.__values__[index] = value
        return self.__values__[index]

    def pop(self, key, default=KeyErrorSingleton):
        index = self.getindex(key)
        if self.__keys__[index] is NoKey:
            if default is not KeyErrorSingleton:
                return default
            else:
                raise KeyError(key)
        old_value = self.__values__[index]
        self.__keys__[index] = NoKey
        self.__values__[index] = NoKey
        return old_value

    def __delitem__(self, key):
        self.pop(key)

    def __repr__(self):
        s = "{"
        for key, value in self.items():
            s += str(key) + ":" + str(value)
            s += ", "
        s += "}"
        return s

    __str__ = __repr__
