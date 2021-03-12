from jsonschema import validate, ValidationError, SchemaError


SCHEMA = {
    'type' : 'object',
    'properties' : {
        'name' : {
            'type' : 'string'
        },
        'age' : {
            'type' : 'number',
        },
        'level': {
            'type': 'string',
            'role': ['FULL_TIME', 'CONTRACTOR']
        }
    },
    'required': ['age','name']
}


def validate_json(json_dict, schema=SCHEMA):
    try:
        print(f'Validating: {json_dict}')
        validate(json_dict, schema)
    except ValidationError as e:
        print(e)
    else:
        print('Is valid')
    print()


validate_json({'name' : 'Bob', 'age' : 20})
validate_json({'name' : 'Bob', 'age' : 20, 'role': 'FULL_TIME'})

validate_json({'name' : 'John', 'age':'Twenty One'})
validate_json({'name' : 'Joe'})
validate_json({'name' : 'Joe', 'age': 21, 'role': 'NOT CONTRACTOR' })
