from dataclasses import dataclass


@dataclass
class Database:
    url: str

    def set_query(self, query):
        print(f'Loading SQL query {query}')

    def commit(self):
        print(f'Committing changes to {self.url}')


def create_db(url):
    return Database(url)


class DBException(Exception):
    def __init__(self, message):
        super().__init__(message)
