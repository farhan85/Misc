#!/usr/bin/env python3

import json
from json import JSONEncoder, JSONDecoder


class Occupation(object):
    def __init__(self, company, years):
        self.company = company
        self.years = int(years)

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.company, self.years)


class Person(object):
    def __init__(self, first_name, last_name, age, occupation):
        self.first_name = first_name
        self.last_name = last_name
        self.age = int(age)
        self.occupation = occupation

    def __repr__(self):
        return '{}({}, {}, {}, {})'.format(self.__class__.__name__, self.first_name,
                self.last_name, self.age, self.occupation)


class OccupationSerializer(JSONEncoder):
    def default(self, o):
        if isinstance(o, Occupation):
            d = {'__class__': Occupation.__name__}
            d.update((k,v) for k,v in o.__dict__.items())
            return d
        else:
            return super().default(o)


class OccupationDeserializer(JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object)

    def dict_to_object(self, d):
        if d.get('__class__') == Occupation.__name__:
            return Occupation(d['company'], d['years'])
        else:
            return d


class PersonSerializer(JSONEncoder):
    def default(self, o):
        if isinstance(o, Person):
            return {
                '__class__': Person.__name__,
                'first_name': o.first_name,
                'last_name': o.last_name,
                'age': o.age,
                'occupation': json.dumps(o.occupation, cls=OccupationSerializer),
            }
        else:
            return super().default(o)


class PersonDeserializer(JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object)

    def dict_to_object(self, d):
        if d.get('__class__') == Person.__name__:
            return Person(d['first_name'],
                          d['last_name'],
                          d['age'],
                          json.loads(d['occupation'], cls=OccupationDeserializer))
        else:
            return d


if __name__ == '__main__':
    person = Person('John', 'Doe', 23, Occupation('SomeCompany', 2))
    person_str = json.dumps(person, cls=PersonSerializer)
    print('JSON string: ', person_str)

    print('Deserialized object: ', json.loads(person_str, cls=PersonDeserializer))
