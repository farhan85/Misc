#!/usr/bin/env python3

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


@dataclass_json
@dataclass
class Person(object):
    user_id: str
    first_name: str
    last_name: str
    gender: str
    age: int


db = TinyDB(storage=MemoryStorage)

person = Person('123', 'John', 'Doe', 'male', 23)
db.insert(person.to_dict())

PersonQuery = Query()
print(db.search(PersonQuery.first_name == 'John'))

person2 = Person.from_dict(db.get(PersonQuery.first_name == 'John'))
print(person2)
person2.first_name = 'Jane'
person2.gender = 'female'
person2.age = 25
db.update(person2.to_dict(), PersonQuery.user_id == person2.user_id)

print(db.search(PersonQuery.user_id == person2.user_id))
