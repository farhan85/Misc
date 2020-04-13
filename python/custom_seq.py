#!/usr/bin/env python3

from itertools import chain, islice

class Team(object):
    def __init__(self, members=None, staff=None):
        self.members = list(members) if members is not None else []
        self.staff = list(staff) if staff is not None else []

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self._slice(key.start, key.stop, key.step)

        if isinstance(key, int):
            return self._index(key)

    def _index(self, idx):
        if idx < len(self.members):
            return self.members[idx]
        elif idx < self.__len__():
            return self.staff[idx - len(self.members)]
        else:
            raise IndexError('{} index out of range'.format(self.__class__.__name__))

    def _slice(self, start, stop, step):
        return list(islice(chain(self.members, self.staff), start, stop, step))

    def __len__(self):
        return len(self.members) + len(self.staff)


team = Team(['John', 'Jack', 'Laura', 'Lisa'],
            ['Bob', 'Barry', 'Amanda', 'Anna'])

for idx, member in enumerate(team):
    print(idx, member)

print()

print('team[3]:', team[3])
print('team[4]:', team[4])
print('len(team):', len(team))
print('team[2:6]:', team[2:6])
print('team[9]:', team[9])
