#!/usr/bin/env python3

import json
import orjson
from datetime import date, datetime, timezone


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        # Unknown object. Let the base class default method raise the TypeError
        return super().default(obj)


class DateTimeDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    def object_hook(self, obj):
        for k, v in obj.items():
            if k == 'timestamp':
                try:
                    obj[k] = datetime.fromisoformat(v)
                except ValueError as e:
                    print(f'Failed to convert "{v}" to datetime. Leaving as string. Reason: {e}')
                    pass
        return obj


def json_tostr(obj):
    return json.dumps(obj, indent=2, cls=DateTimeEncoder)


def json_fromstr(s):
    return json.loads(s, cls=DateTimeDecoder)


def orjson_tostr(obj):
    options = orjson.OPT_INDENT_2 | orjson.OPT_OMIT_MICROSECONDS | orjson.OPT_UTC_Z
    return orjson.dumps(obj, option=options).decode("utf-8")


if __name__ == '__main__':
    obj = {
        'description': 'testing serializing/deserializing json with datetime',
        'timestamp': datetime.now(timezone.utc)
    }

    print(json_tostr(obj))
    print(orjson_tostr(obj))

    s = json_tostr(obj)
    print(json_fromstr(s))
