#!/usr/bin/env python3

from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

#db = TinyDB('db.json', indent=4)
db = TinyDB(storage=MemoryStorage)

db.insert({'name': 'John', 'age': 22})

User = Query()
print(db.search(User.name == 'John'))

db.update({'gender': 'male'}, User.name == 'John')
print(db.search(User.name == 'John'))

db.remove(User.name.search('John'))
