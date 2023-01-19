#
# This is NOT an example of how to use a database to store objects. The purpose
# of this file is to show how to patch function calls and mock objects in unit
# tests with pytest.
#

import datetime
from pytestexample.db_utils import create_db, DBException


class User:
    def __init__(self):
        self.db = create_db('https://mydb.test:80')
        self.current_id = 1

    def new_user(self, first_name, last_name):
        user_id = f'user-{self.current_id}'
        create_date = datetime.datetime.now()
        create_date_s = create_date.strftime("%Y-%d-%mT%H:%M")
        self.db.set_query(("INSERT INTO users "
                           "(id, firstname, lastname, create_date) "
                           f"VALUES ('{user_id}', '{first_name}', '{last_name}', '{create_date_s}');"))
        self.db.commit()
        self.current_id += 1
        print(f'Saved user with ID: {user_id}')

    def update_name(self, user_id, first_name, last_name):
        self.db.set_query(("UPDATE users "
                          f"SET firstname='{first_name}', lastname='{last_name}' "
                          f"WHERE id='{user_id}';"))
        try:
            self.db.commit()
        except DBException as e:
            raise RuntimeError(f'Failed to update user {first_name} {last_name}') from e
