from deepdiff import DeepDiff


print(DeepDiff({'name': 'Bob', 'age': 20},
               {'name': 'Bob', 'age': 20}))

print(DeepDiff({'name': 'Bob', 'age': 20},
               {'name': 'Bob', 'age': 90}))


print(DeepDiff({'name': 'Bob', 'roles': ['role1', 'role3']},
               {'name': 'Bob', 'roles': ['role1', 'role3']},))

print(DeepDiff({'name': 'Bob', 'roles': ['role1', 'role3']},
               {'name': 'Bob', 'roles': ['role2']}))


print(DeepDiff({'name': 'Bob', 'props': {'a': 1, 'b': 2}},
               {'name': 'Bob', 'props': {'a': 1, 'b': 2}}))

print(DeepDiff({'name': 'Bob', 'props': {'a': 1, 'b': 2}},
               {'name': 'Bob', 'props': {'a': 1, 'c': 3}}))
