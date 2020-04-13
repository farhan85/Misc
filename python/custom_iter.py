#!/usr/bin/env python3

class Team(object):
    def __init__(self, members=None, staff=None):
        self.members = list(members) if members is not None else []
        self.staff = list(staff) if staff is not None else []

    def __iter__(self):
        return TeamIterator(self)


class TeamIterator(object):
    def __init__(self, team):
        self.team_list = [team.members, team.staff]
        self.team_list_index = 0
        self.index = -1

    def __next__(self):
        self.index += 1
        if self.index == len(self.team_list[self.team_list_index]):
            self.team_list_index += 1
            self.index = 0

        if self.team_list_index == len(self.team_list):
            raise StopIteration

        return self.team_list[self.team_list_index][self.index]


team = Team(['John', 'Jack', 'Laura', 'Lisa'],
            ['Bob', 'Barry', 'Amanda', 'Anna'])
for member in team:
    print(member)
