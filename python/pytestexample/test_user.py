#
# Run with:
# > pytest test_user.py
#
# If you want to display stdout during the tests, then run:
# > pytest test_user.py --capture=no
#

import pytest
from datetime import datetime
from unittest.mock import call, Mock

from .db_utils import Database, DBException
from .user import User


@pytest.fixture
def mock_db():
    return Mock(spec=Database)


@pytest.fixture
def mock_create_db(monkeypatch, mock_db):
    create_db_func = Mock(return_value=mock_db)
    monkeypatch.setattr('pytestexample.user.create_db', create_db_func)
    return create_db_func


@pytest.fixture
def mock_datetime(monkeypatch):
    dt = datetime(2021, 1, 18, 9, 30)
    datetime_module = Mock()
    datetime_module.datetime.now.return_value = dt
    monkeypatch.setattr('pytestexample.user.datetime', datetime_module)
    return dt


def test_GIVEN_User_WHEN_creating_user_obj_THEN_call_db_with_connection_str(mock_create_db):
    user = User()
    mock_create_db.assert_called_with('https://mydb.test:80')


def test_GIVEN_firstname_lastname_WHEN_calling_new_user_THEN_run_insert_query(mock_create_db, mock_db, mock_datetime):
    first_name = 'John'
    last_name = 'Doe'
    create_date_s = mock_datetime.strftime("%Y-%d-%mT%H:%M")
    expected_query = ' '.join([
        'INSERT INTO users (id, firstname, lastname, create_date)',
        f"VALUES ('user-1', '{first_name}', '{last_name}', '{create_date_s}');"
    ])

    user = User()
    user.new_user(first_name, last_name)

    mock_db.set_query.assert_called_with(expected_query)
    mock_db.commit.assert_called()


def test_GIVEN_two_users_WHEN_calling_new_user_THEN_run_insert_query_with_different_userids(mock_create_db, mock_db, mock_datetime):
    first_name_1 = 'John'
    last_name_1 = 'Doe'
    first_name_2 = 'Bob'
    last_name_2 = 'Smith'
    create_date_s = mock_datetime.strftime("%Y-%d-%mT%H:%M")
    expected_query_1 = ' '.join([
        'INSERT INTO users (id, firstname, lastname, create_date)',
        f"VALUES ('user-1', '{first_name_1}', '{last_name_1}', '{create_date_s}');"
    ])
    expected_query_2 = ' '.join([
        'INSERT INTO users (id, firstname, lastname, create_date)',
        f"VALUES ('user-2', '{first_name_2}', '{last_name_2}', '{create_date_s}');"
    ])
    expected_calls = [call(expected_query_1), call(expected_query_2)]

    user = User()
    user.new_user(first_name_1, last_name_1)
    user.new_user(first_name_2, last_name_2)

    mock_db.set_query.assert_has_calls(expected_calls)
    mock_db.commit.assert_called()


def test_GIVEN_userid_firstname_lastname_WHEN_calling_udpate_name_THEN_run_update_query(mock_create_db, mock_db):
    user_id = 'user-1'
    first_name = 'John'
    last_name = 'Doe'
    expected_query = ' '.join([
        'UPDATE users',
        f"SET firstname='{first_name}', lastname='{last_name}'",
        f"WHERE id='{user_id}';"
    ])

    user = User()
    user.update_name(user_id, first_name, last_name)

    mock_db.set_query.assert_called_with(expected_query)
    mock_db.commit.assert_called()


def test_GIVEN_db_throws_exception_WHEN_calling_udpate_name_THEN_throw_runtime_error(mock_create_db, mock_db):
    mock_db.commit.side_effect = DBException('Invalid user ID given')
    user = User()
    with pytest.raises(RuntimeError):
        user.update_name('user-1', 'John', 'Doe')
