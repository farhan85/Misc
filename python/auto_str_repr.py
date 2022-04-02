import inspect


def auto_str(cls):
    def to_str(lst): return ', '.join(f'{k}={v}' for k, v in lst)

    def __str__(self):
        attributes = to_str(self.__dict__.items())
        properties = to_str((p[0], p[1].fget(self))
                            for p in inspect.getmembers(cls, lambda obj: isinstance(obj, property)))

        return f'{type(self).__name__}({attributes}, {properties})'
    cls.__str__ = __str__
    return cls


def auto_repr(cls):
    def __repr__(self):
        attributes = ', '.join(f'{k}={repr(v)}' for k, v in self.__dict__.items())
        return f'{type(self).__name__}({attributes})'
    cls.__repr__ = __repr__
    return cls


@auto_str
@auto_repr
class Person:
    def __init__(self, first_name, last_name, age):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age

    @property
    def is_adult(self):
        return self.age > 18


if __name__ == '__main__':
    person1 = Person('John', 'Doe', 30)
    person2 = Person('Bob', 'Smith', 16)
    print(person1)
    print(person2)
    print(repr(person1))
    print(repr(person2))
